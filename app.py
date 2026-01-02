import os
import time
import re
import unicodedata
from flask import Flask, request, jsonify, render_template_string
from supabase import create_client, Client
from dotenv import load_dotenv

# Carrega variáveis de ambiente (.env)
load_dotenv()

app = Flask(__name__)

# Configurações do Sistema
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def limpar_nome_arquivo(nome):
    """Remove acentos e caracteres especiais dos nomes dos arquivos"""
    nome = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    nome = re.sub(r'[^a-zA-Z0-9._-]', '_', nome)
    return nome

def upload_imagem_supabase(file, prefixo):
    """Faz o upload para o storage e retorna o nome final e a URL pública"""
    nome_final = f"{prefixo}_{int(time.time())}_{limpar_nome_arquivo(file.filename)}"
    supabase.storage.from_(BUCKET_NAME).upload(
        path=nome_final, 
        file=file.read(), 
        file_options={"content-type": file.content_type}
    )
    url = supabase.storage.from_(BUCKET_NAME).get_public_url(nome_final)
    return nome_final, url

@app.before_request
def check_auth():
    """Validação de senha para todas as rotas da API"""
    if request.path.startswith("/api"):
        password = request.headers.get("x-app-password")
        if password != APP_PASSWORD:
            return jsonify({"error": "Acesso não autorizado"}), 401

@app.route("/")
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Serena Admin | Painel de Controle</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
        
        body { 
            font-family: 'Plus Jakarta Sans', sans-serif; 
            background: #f8fafc; 
            color: #1e293b;
        }

        .tab-btn {
            padding: 12px 24px;
            border-radius: 16px;
            font-weight: 700;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #64748b;
        }

        .tab-btn.active-galeria { background: #4f46e5; color: white; box-shadow: 0 10px 15px -3px rgba(79, 70, 229, 0.3); }
        .tab-btn.active-promo { background: #f97316; color: white; box-shadow: 0 10px 15px -3px rgba(249, 115, 22, 0.3); }

        .glass-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 28px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        .glass-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05);
        }

        .modal-blur {
            backdrop-filter: blur(12px);
            background: rgba(15, 23, 42, 0.6);
        }

        input, textarea {
            border: 2px solid #f1f5f9 !important;
            transition: all 0.2s ease;
        }

        input:focus, textarea:focus {
            border-color: #e2e8f0 !important;
            box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1) !important;
            background: white !important;
        }
    </style>
</head>
<body class="min-h-screen pb-20">

    <div id="toast" class="fixed top-6 left-1/2 -translate-x-1/2 z-[200] px-6 py-3 rounded-full font-bold shadow-2xl opacity-0 transition-all pointer-events-none text-sm"></div>

    <div id="loginPage" class="fixed inset-0 flex flex-col items-center justify-center bg-white z-[150]">
        <div class="w-full max-w-sm px-8 text-center">
            <div class="w-20 h-20 bg-indigo-600 rounded-[2rem] flex items-center justify-center shadow-xl mx-auto mb-6 rotate-3">
                <i data-lucide="shield-check" class="text-white w-10 h-10 -rotate-3"></i>
            </div>
            <h1 class="text-3xl font-extrabold text-slate-900 mb-2">Painel Serena</h1>
            <p class="text-slate-400 mb-8 font-medium">Controle de Conteúdo Jundiaí</p>
            <input type="password" id="pwdInput" class="w-full p-5 bg-slate-50 border-none rounded-2xl text-center text-2xl font-bold outline-none mb-4" placeholder="••••">
            <button onclick="handleLogin()" class="w-full bg-slate-900 text-white p-5 rounded-2xl font-bold hover:bg-black transition-all">Acessar Sistema</button>
        </div>
    </div>

    <div id="mainPage" class="hidden">
        <header class="fixed top-0 left-0 right-0 z-40 p-4">
            <div class="max-w-5xl mx-auto flex items-center justify-between bg-white/80 backdrop-blur-xl border border-white/40 p-3 rounded-[2rem] shadow-lg">
                <div class="flex items-center gap-3 pl-4">
                    <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
                        <i data-lucide="zap" class="w-5 h-5"></i>
                    </div>
                    <span class="font-extrabold text-lg hidden md:block">Serena Admin</span>
                </div>

                <nav class="flex gap-2 bg-slate-100/50 p-1.5 rounded-2xl">
                    <button onclick="switchTab('galeria')" id="btn-galeria" class="tab-btn active-galeria">
                        <i data-lucide="image"></i> Galeria
                    </button>
                    <button onclick="switchTab('promocoes')" id="btn-promocoes" class="tab-btn">
                        <i data-lucide="flame"></i> Promos
                    </button>
                </nav>

                <button onclick="logout()" class="w-12 h-12 flex items-center justify-center text-slate-400 hover:text-red-500 transition-colors">
                    <i data-lucide="log-out"></i>
                </button>
            </div>
        </header>

        <main class="max-w-5xl mx-auto px-6 mt-32">
            
            <div id="tab-galeria" class="space-y-8">
                <section class="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-sm">
                    <h3 class="text-xl font-extrabold mb-6 flex items-center gap-2"><i data-lucide="plus-circle" class="text-indigo-600"></i> Adicionar à Galeria</h3>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="relative">
                            <input type="file" id="fileGaleria" class="w-full p-4 bg-slate-50 rounded-2xl text-sm border-2 border-dashed border-slate-200">
                        </div>
                        <input type="text" id="tagsGaleria" placeholder="Tags (ex: Unhas, Noivas, Preços)" class="w-full p-4 bg-slate-50 rounded-2xl outline-none font-semibold">
                    </div>
                    <button onclick="uploadGaleria()" id="btnUpGal" class="w-full mt-6 bg-indigo-600 text-white py-5 rounded-2xl font-extrabold hover:bg-indigo-700 shadow-lg shadow-indigo-100 transition-all flex items-center justify-center gap-2">
                        <i data-lucide="upload-cloud"></i> Publicar Foto
                    </button>
                </section>
                <div id="list-galeria" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"></div>
            </div>

            <div id="tab-promocoes" class="hidden space-y-8">
                <section class="bg-white rounded-[2.5rem] p-8 border border-slate-100 shadow-sm">
                    <h3 class="text-xl font-extrabold mb-6 flex items-center gap-2"><i data-lucide="megaphone" class="text-orange-500"></i> Nova Promoção Ativa</h3>
                    <div class="space-y-4">
                        <input type="file" id="filePromo" class="w-full p-4 bg-slate-50 rounded-2xl text-sm border-2 border-dashed">
                        <input type="text" id="tituloPromo" placeholder="Título da Campanha" class="w-full p-4 bg-slate-50 rounded-2xl font-bold outline-none">
                        <textarea id="textoPromo" placeholder="Descrição da oferta para a Serena falar..." class="w-full p-4 bg-slate-50 rounded-2xl h-32 outline-none font-medium"></textarea>
                        <input type="text" id="tagPromo" placeholder="Tag única (ex: promo_natal)" class="w-full p-4 bg-slate-50 rounded-2xl outline-none">
                    </div>
                    <button onclick="uploadPromo()" id="btnUpPromo" class="w-full mt-6 bg-orange-500 text-white py-5 rounded-2xl font-extrabold hover:bg-orange-600 shadow-lg shadow-orange-100 transition-all">
                        Ativar Campanha Agora
                    </button>
                </section>
                <div id="list-promocoes" class="grid grid-cols-1 gap-6"></div>
            </div>
        </main>
    </div>

    <div id="editModal" class="fixed inset-0 z-[200] hidden flex items-center justify-center p-4 modal-blur">
        <div class="bg-white max-w-lg w-full rounded-[3rem] p-10 shadow-2xl overflow-y-auto max-h-[90vh]">
            <div class="flex justify-between items-center mb-8">
                <h3 class="text-2xl font-black flex items-center gap-3"><i data-lucide="edit-3" class="text-indigo-600"></i> Ajustar Dados</h3>
                <button onclick="closeModal('editModal')" class="bg-slate-100 p-2 rounded-full text-slate-500 hover:bg-red-50 hover:text-red-500 transition-all"><i data-lucide="x"></i></button>
            </div>
            
            <div class="mb-6 group relative">
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Imagem Atual</p>
                <img id="imgCurrent" src="" class="w-full h-56 object-cover rounded-[2rem] border-4 border-slate-50 shadow-inner">
            </div>

            <div class="space-y-6">
                <div class="bg-indigo-50/50 p-6 rounded-3xl border border-indigo-100">
                    <label class="text-xs font-black text-indigo-600 uppercase mb-2 block">Deseja trocar a imagem?</label>
                    <input type="file" id="editFile" class="w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-bold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700">
                </div>

                <div id="editFormFields" class="space-y-4"></div>
            </div>

            <div class="flex gap-4 mt-10">
                <button onclick="closeModal('editModal')" class="flex-1 py-4 bg-slate-100 rounded-2xl font-bold text-slate-500 hover:bg-slate-200 transition">Voltar</button>
                <button id="saveEditBtn" class="flex-1 py-4 bg-slate-900 text-white rounded-2xl font-bold shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all">Salvar Alterações</button>
            </div>
        </div>
    </div>

    <script>
        const getAuth = () => localStorage.getItem('planeta_auth');

        function notify(msg, type='success') {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.className = `fixed top-6 left-1/2 -translate-x-1/2 z-[200] px-6 py-3 rounded-full font-bold shadow-2xl opacity-100 transition-all ${type==='success'?'bg-slate-900 text-white':'bg-red-500 text-white'}`;
            setTimeout(() => t.style.opacity = '0', 3000);
        }

        function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

        async function handleLogin() {
            const pwd = document.getElementById('pwdInput').value;
            const res = await fetch('/api/images', { headers: {'x-app-password': pwd} });
            if (res.ok) { localStorage.setItem('planeta_auth', pwd); location.reload(); }
            else { notify("Senha inválida", "error"); }
        }

        function switchTab(tab) {
            const isGal = tab === 'galeria';
            document.getElementById('tab-galeria').classList.toggle('hidden', !isGal);
            document.getElementById('tab-promocoes').classList.toggle('hidden', isGal);
            
            document.getElementById('btn-galeria').className = `tab-btn ${isGal ? 'active-galeria' : ''}`;
            document.getElementById('btn-promocoes').className = `tab-btn ${!isGal ? 'active-promo' : ''}`;
            
            isGal ? loadGaleria() : loadPromos();
        }

        async function loadGaleria() {
            const res = await fetch('/api/images', { headers: {'x-app-password': getAuth()} });
            const data = await res.json();
            document.getElementById('list-galeria').innerHTML = data.map(img => `
                <div class="glass-card group overflow-hidden p-3">
                    <img src="${img.url}" class="w-full h-64 object-cover rounded-[1.5rem] mb-4">
                    <div class="px-2 pb-2">
                        <div class="flex flex-wrap gap-2 mb-4">
                            ${img.tags.split(',').map(t => `<span class="bg-slate-100 text-slate-500 text-[9px] px-2 py-1 rounded-lg font-black uppercase">#${t.trim()}</span>`).join('')}
                        </div>
                        <div class="flex gap-2">
                            <button onclick='openEditGaleria(${JSON.stringify(img)})' class="flex-1 py-3 bg-indigo-50 text-indigo-600 rounded-xl font-bold text-xs hover:bg-indigo-600 hover:text-white transition-all">Editar Dados</button>
                            <button onclick="deleteItem('images', '${img.name}')" class="p-3 bg-red-50 text-red-500 rounded-xl hover:bg-red-500 hover:text-white transition-all"><i data-lucide="trash-2" class="w-4 h-4"></i></button>
                        </div>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }

        async function loadPromos() {
            const res = await fetch('/api/promotions', { headers: {'x-app-password': getAuth()} });
            const data = await res.json();
            document.getElementById('list-promocoes').innerHTML = data.map(p => `
                <div class="glass-card p-5 flex flex-col md:flex-row items-center gap-6">
                    <img src="${p.url_imagem}" class="w-full md:w-32 h-32 object-cover rounded-2xl shadow-md">
                    <div class="flex-1 text-center md:text-left">
                        <span class="text-[9px] bg-orange-100 text-orange-600 px-3 py-1 rounded-full font-black uppercase tracking-widest">#${p.tag}</span>
                        <h4 class="text-lg font-extrabold mt-2 mb-1">${p.titulo}</h4>
                        <p class="text-slate-400 text-sm line-clamp-2">${p.texto_informativo}</p>
                    </div>
                    <div class="flex md:flex-col gap-2 w-full md:w-auto">
                        <button onclick='openEditPromo(${JSON.stringify(p)})' class="flex-1 md:flex-none p-4 bg-slate-900 text-white rounded-2xl font-bold text-xs hover:bg-black transition-all">Ajustar</button>
                        <button onclick="deleteItem('promotions', '${p.nome_arquivo}')" class="p-4 bg-red-50 text-red-500 rounded-2xl hover:bg-red-500 hover:text-white transition-all"><i data-lucide="trash-2" class="w-5 h-5"></i></button>
                    </div>
                </div>
            `).join('');
            lucide.createIcons();
        }

        // FUNÇÃO PARA ABRIR EDIÇÃO DA GALERIA
        function openEditGaleria(img) {
            document.getElementById('imgCurrent').src = img.url;
            document.getElementById('editFile').value = ""; // Limpa campo de arquivo
            document.getElementById('editFormFields').innerHTML = `
                <div>
                    <label class="text-xs font-bold text-slate-400 uppercase ml-2 mb-1 block">Tags de Busca</label>
                    <input type="text" id="fieldTags" value="${img.tags}" class="w-full p-4 bg-slate-50 rounded-2xl font-bold outline-none">
                </div>
            `;
            document.getElementById('editModal').classList.remove('hidden');
            document.getElementById('saveEditBtn').onclick = () => saveEdit('images', img.name);
        }

        // FUNÇÃO PARA ABRIR EDIÇÃO DE PROMO
        function openEditPromo(p) {
            document.getElementById('imgCurrent').src = p.url_imagem;
            document.getElementById('editFile').value = "";
            document.getElementById('editFormFields').innerHTML = `
                <input type="text" id="fieldTitulo" value="${p.titulo}" class="w-full p-4 bg-slate-50 rounded-2xl font-bold mb-2">
                <textarea id="fieldTexto" class="w-full p-4 bg-slate-50 rounded-2xl h-32 mb-2 font-medium">${p.texto_informativo}</textarea>
                <input type="text" id="fieldTag" value="${p.tag}" class="w-full p-4 bg-slate-50 rounded-2xl">
            `;
            document.getElementById('editModal').classList.remove('hidden');
            document.getElementById('saveEditBtn').onclick = () => saveEdit('promotions', p.nome_arquivo);
        }

        // SALVAMENTO COM LÓGICA DE TROCA DE IMAGEM
        async function saveEdit(type, oldName) {
            const btn = document.getElementById('saveEditBtn');
            btn.disabled = true; btn.innerText = "Salvando...";

            const fd = new FormData();
            fd.append('old_name', oldName);
            
            const fileInput = document.getElementById('editFile');
            if(fileInput.files[0]) {
                fd.append('image', fileInput.files[0]);
            }

            if(type === 'images') {
                fd.append('tags', document.getElementById('fieldTags').value);
            } else {
                fd.append('titulo', document.getElementById('fieldTitulo').value);
                fd.append('texto', document.getElementById('fieldTexto').value);
                fd.append('tag', document.getElementById('fieldTag').value);
            }

            const res = await fetch(`/api/${type}/update`, {
                method: 'POST',
                headers: {'x-app-password': getAuth()},
                body: fd
            });

            if(res.ok) {
                notify("Registro atualizado com sucesso!");
                closeModal('editModal');
                type === 'images' ? loadGaleria() : loadPromos();
            } else {
                notify("Erro ao atualizar", "error");
            }
            btn.disabled = false; btn.innerText = "Salvar Alterações";
        }

        async function uploadGaleria() {
            const file = document.getElementById('fileGaleria').files[0];
            if(!file) return notify("Selecione uma foto!", "error");
            const fd = new FormData();
            fd.append('image', file);
            fd.append('tags', document.getElementById('tagsGaleria').value);
            await fetch('/api/upload', { method: 'POST', headers: {'x-app-password': getAuth()}, body: fd });
            notify("Galeria Atualizada!"); loadGaleria();
        }

        async function uploadPromo() {
            const file = document.getElementById('filePromo').files[0];
            if(!file) return notify("Selecione uma imagem!", "error");
            const fd = new FormData();
            fd.append('image', file);
            fd.append('titulo', document.getElementById('tituloPromo').value);
            fd.append('texto', document.getElementById('textoPromo').value);
            fd.append('tag', document.getElementById('tagPromo').value);
            await fetch('/api/promotions', { method: 'POST', headers: {'x-app-password': getAuth()}, body: fd });
            notify("Promoção Ativada!"); loadPromos();
        }

        async function deleteItem(type, name) {
            if(!confirm("Tem certeza? Esta ação apagará a imagem para sempre.")) return;
            await fetch(`/api/${type}/${name}`, { method: 'DELETE', headers: {'x-app-password': getAuth()} });
            type === 'images' ? loadGaleria() : loadPromos();
            notify("Removido com sucesso!");
        }

        function logout() { localStorage.removeItem('planeta_auth'); location.reload(); }
        
        window.onload = () => { 
            if(getAuth()) { 
                document.getElementById('loginPage').classList.add('hidden'); 
                document.getElementById('mainPage').classList.remove('hidden'); 
                loadGaleria(); 
            } 
            lucide.createIcons(); 
        };
    </script>
</body>
</html>
    """)

# --- ROTAS DA API NO BACKEND (PYTHON) ---

@app.route("/api/images", methods=["GET"])
def list_images():
    res = supabase.table("galeria_tags_jundiai").select("*").order("created_at", desc=True).execute()
    return jsonify([{"name": i['nome_arquivo'], "url": i['url_imagem'], "tags": i['tags']} for i in res.data])

@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files['image']
    tags = request.form.get('tags', '')
    nome, url = upload_imagem_supabase(file, "gal")
    supabase.table("galeria_tags_jundiai").insert({"nome_arquivo": nome, "tags": tags, "url_imagem": url}).execute()
    return jsonify({"status": "ok"})

@app.route("/api/images/update", methods=["POST"])
def update_image():
    old_name = request.form.get('old_name')
    tags = request.form.get('tags')
    
    dados_update = {"tags": tags}
    
    # LÓGICA DE TROCA DE IMAGEM
    if 'image' in request.files:
        # 1. Remove arquivo físico antigo do Storage
        supabase.storage.from_(BUCKET_NAME).remove([old_name])
        # 2. Sobe o novo arquivo
        novo_nome, nova_url = upload_imagem_supabase(request.files['image'], "gal")
        # 3. Atualiza os nomes no banco de dados
        dados_update["nome_arquivo"] = novo_nome
        dados_update["url_imagem"] = nova_url
    
    supabase.table("galeria_tags_jundiai").update(dados_update).eq("nome_arquivo", old_name).execute()
    return jsonify({"status": "updated"})

@app.route("/api/images/<name>", methods=["DELETE"])
def delete_image(name):
    supabase.table("galeria_tags_jundiai").delete().eq("nome_arquivo", name).execute()
    supabase.storage.from_(BUCKET_NAME).remove([name])
    return jsonify({"status": "deleted"})

@app.route("/api/promotions", methods=["GET"])
def list_promotions():
    res = supabase.table("promocoes_ativas_jundiai").select("*").order("created_at", desc=True).execute()
    return jsonify(res.data)

@app.route("/api/promotions", methods=["POST"])
def upload_promotion():
    file = request.files['image']
    nome, url = upload_imagem_supabase(file, "promo")
    supabase.table("promocoes_ativas_jundiai").insert({
        "titulo": request.form.get('titulo'),
        "texto_informativo": request.form.get('texto'),
        "tag": request.form.get('tag'),
        "url_imagem": url,
        "nome_arquivo": nome
    }).execute()
    return jsonify({"status": "ok"})

@app.route("/api/promotions/update", methods=["POST"])
def update_promotion():
    old_name = request.form.get('old_name')
    dados_update = {
        "titulo": request.form.get('titulo'),
        "texto_informativo": request.form.get('texto'),
        "tag": request.form.get('tag')
    }
    
    # LÓGICA DE TROCA DE IMAGEM
    if 'image' in request.files:
        supabase.storage.from_(BUCKET_NAME).remove([old_name])
        novo_nome, nova_url = upload_imagem_supabase(request.files['image'], "promo")
        dados_update["nome_arquivo"] = novo_nome
        dados_update["url_imagem"] = nova_url
    
    supabase.table("promocoes_ativas_jundiai").update(dados_update).eq("nome_arquivo", old_name).execute()
    return jsonify({"status": "updated"})

@app.route("/api/promotions/<name>", methods=["DELETE"])
def delete_promotion(name):
    supabase.table("promocoes_ativas_jundiai").delete().eq("nome_arquivo", name).execute()
    supabase.storage.from_(BUCKET_NAME).remove([name])
    return jsonify({"status": "deleted"})

if __name__ == "__main__":
    # Rodar o app
    app.run(host="0.0.0.0", port=5000, debug=True)
