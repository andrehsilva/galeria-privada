import os
import time
import re
import unicodedata
from flask import Flask, request, jsonify, render_template_string
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações do Sistema
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Inicialização do Cliente
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def limpar_nome_arquivo(nome):
    nome = unicodedata.normalize('NFKD', nome).encode('ascii', 'ignore').decode('ascii')
    nome = re.sub(r'[^a-zA-Z0-9._-]', '_', nome)
    return nome

@app.before_request
def check_auth():
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
    <title>Planeta Imaginário Jundiaí | Galeria</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
        body { font-family: 'Plus Jakarta Sans', sans-serif; @apply bg-slate-50 text-slate-900; }
        .hidden { display: none !important; }
        .glass { @apply bg-white/90 backdrop-blur-lg border border-slate-200 shadow-xl; }
        .img-square { position: relative; width: 100%; padding-top: 100%; overflow: hidden; border-radius: 1.5rem; }
        .img-square img { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; transition: all 0.5s ease; }
        .img-square:hover img { transform: scale(1.08); filter: brightness(0.8); }
        #toast { transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); transform: translateY(100%) translateX(-50%); }
        #toast.show { transform: translateY(-30px) translateX(-50%); }
    </style>
</head>
<body class="min-h-screen">

    <div id="toast" class="fixed bottom-0 left-1/2 z-[100] px-8 py-4 rounded-2xl font-bold shadow-2xl pointer-events-none opacity-0"></div>

    <div id="modal" class="fixed inset-0 z-[80] hidden flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
        <div class="bg-white max-w-sm w-full rounded-[2rem] p-8 shadow-2xl text-center animate-in zoom-in duration-300">
            <div id="modalIcon" class="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4 bg-red-50 text-red-500">
                <i data-lucide="alert-triangle"></i>
            </div>
            <h3 id="modalTitle" class="text-xl font-bold mb-2">Tem certeza?</h3>
            <p id="modalText" class="text-slate-500 text-sm mb-8"></p>
            <div class="flex gap-3">
                <button onclick="closeModal('modal')" class="flex-1 py-4 rounded-2xl bg-slate-100 font-semibold hover:bg-slate-200 transition">Cancelar</button>
                <button id="confirmBtn" class="flex-1 py-4 rounded-2xl bg-red-500 text-white font-bold hover:bg-red-600 shadow-lg shadow-red-200 transition">Excluir</button>
            </div>
        </div>
    </div>

    <div id="viewer" onclick="closeModal('viewer')" class="fixed inset-0 z-[90] hidden flex items-center justify-center p-4 bg-slate-950/90 backdrop-blur-md cursor-zoom-out transition-all">
        <button class="absolute top-6 right-6 p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition">
            <i data-lucide="x"></i>
        </button>
        <img id="viewerImg" src="" class="max-w-full max-h-[90vh] rounded-2xl shadow-2xl object-contain animate-in zoom-in duration-300" onclick="event.stopPropagation()">
    </div>

    <div id="loginPage" class="fixed inset-0 flex flex-col items-center justify-center bg-white z-50">
        <div class="w-full max-w-md px-6 text-center">
            <div class="mb-10">
                <div class="w-20 h-20 bg-indigo-600 rounded-[2rem] flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-indigo-200">
                    <i data-lucide="rocket" class="text-white w-10 h-10"></i>
                </div>
                <h1 class="text-3xl font-extrabold text-slate-900 tracking-tight">Planeta Imaginário</h1>
                <p class="text-indigo-600 font-bold uppercase tracking-widest text-xs mt-1">Unidade Jundiaí</p>
            </div>
            <div class="bg-slate-50 p-8 rounded-[2.5rem] border border-slate-100">
                <input type="password" id="pwdInput" class="w-full bg-white border border-slate-200 p-5 rounded-2xl mb-4 outline-none focus:ring-4 focus:ring-indigo-100 transition-all text-center text-xl font-bold" placeholder="Senha de Acesso">
                <button onclick="handleLogin()" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white p-5 rounded-2xl font-bold text-lg shadow-xl shadow-indigo-100 transition-all active:scale-[0.98]">
                    Acessar Galeria
                </button>
            </div>
        </div>
    </div>

    <div id="mainPage" class="hidden">
        <header class="sticky top-0 z-40 bg-white/80 backdrop-blur-md border-b border-slate-100 px-6 py-5">
            <div class="max-w-6xl mx-auto flex justify-between items-center">
                <div class="flex items-center gap-3">
                    <div class="w-10 h-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white">
                        <i data-lucide="rocket" class="text-white w-6 h-6"></i>
                    </div>
                    <div>
                        <h2 class="font-extrabold text-lg leading-none">Galeria - Planeta Jundiaí</h2>
                    </div>
                </div>
                <button onclick="logout()" class="p-3 text-slate-400 hover:text-red-500 transition"><i data-lucide="log-out"></i></button>
            </div>
        </header>

        <main class="max-w-6xl mx-auto px-6 pt-10 pb-24">
            <section class="max-w-2xl mx-auto mb-16">
                <div class="bg-white p-6 rounded-[2.5rem] shadow-sm border border-slate-100 flex flex-col md:flex-row gap-4 items-center">
                    <input type="file" id="fileInput" accept="image/*" class="flex-1 text-sm text-slate-500 file:mr-4 file:py-3 file:px-6 file:rounded-xl file:border-0 file:text-sm file:font-bold file:bg-indigo-50 file:text-indigo-700 cursor-pointer">
                    <button id="upBtn" onclick="doUpload()" class="w-full md:w-auto bg-indigo-600 text-white px-10 py-4 rounded-2xl font-bold hover:bg-indigo-700 transition shadow-lg shadow-indigo-100 flex items-center justify-center gap-2">
                        <i data-lucide="upload-cloud"></i> Subir Foto
                    </button>
                </div>
            </section>

            <div id="gallery" class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6"></div>
        </main>
    </div>

    <script>
        function notify(msg, type='success') {
            const t = document.getElementById('toast');
            t.innerText = msg;
            t.className = `fixed bottom-0 left-1/2 z-[100] px-8 py-4 rounded-2xl font-bold shadow-2xl opacity-100 show ${type==='success'?'bg-slate-900 text-white':'bg-red-500 text-white'}`;
            setTimeout(() => t.classList.remove('opacity-100', 'show'), 3000);
        }

        async function handleLogin() {
            const pwd = document.getElementById('pwdInput').value;
            if(!pwd) return;
            const res = await fetch('/api/images', { headers: {'x-app-password': pwd} });
            if (res.ok) {
                localStorage.setItem('planeta_auth', pwd);
                showMain();
            } else { notify("Senha incorreta!", "error"); }
        }

        function showMain() {
            document.getElementById('loginPage').classList.add('hidden');
            document.getElementById('mainPage').classList.remove('hidden');
            loadImages();
        }

        function logout() {
            localStorage.removeItem('planeta_auth');
            location.reload();
        }

        function closeModal(id) { document.getElementById(id).classList.add('hidden'); }
        
        function openViewer(url) {
            const viewerImg = document.getElementById('viewerImg');
            viewerImg.src = url;
            document.getElementById('viewer').classList.remove('hidden');
        }

        async function loadImages() {
            const gallery = document.getElementById('gallery');
            const pwd = localStorage.getItem('planeta_auth');
            gallery.innerHTML = Array(5).fill('<div class="img-square bg-slate-100 animate-pulse"></div>').join('');
            
            try {
                const res = await fetch('/api/images', { headers: {'x-app-password': pwd} });
                const data = await res.json();
                
                gallery.innerHTML = data.length ? data.map(img => `
                    <div class="group relative rounded-[1.5rem] bg-white border border-slate-100 shadow-sm overflow-hidden">
                        <div class="absolute top-0 left-0 right-0 z-10 p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            <div class="bg-white/80 backdrop-blur-sm px-3 py-1 rounded-full border border-slate-200 shadow-sm">
                                <p class="text-[10px] font-bold text-slate-600 truncate text-center">${img.name}</p>
                            </div>
                        </div>
                        
                        <div class="img-square">
                            <img src="${img.url}?t=${Date.now()}" loading="lazy">
                        </div>
                        
                        <div class="absolute inset-0 bg-indigo-900/40 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-4">
                            <div class="flex gap-2">
                                <button onclick="openViewer('${img.url}')" class="p-3 bg-white rounded-xl shadow-lg hover:bg-slate-50 transition" title="Ver foto">
                                    <i data-lucide="eye" class="w-4 h-4 text-indigo-600"></i>
                                </button>
                                <button onclick="copyURL('${img.url}')" class="flex-1 bg-white p-3 rounded-xl shadow-lg hover:bg-slate-50 transition flex items-center justify-center gap-2">
                                    <i data-lucide="copy" class="w-4 h-4 text-indigo-600"></i>
                                    <span class="text-[10px] font-bold text-indigo-600 uppercase">Copiar</span>
                                </button>
                                <button onclick="askDelete('${img.name}')" class="bg-red-500 p-3 rounded-xl shadow-lg hover:bg-red-600 transition">
                                    <i data-lucide="trash-2" class="w-4 h-4 text-white"></i>
                                </button>
                            </div>
                        </div>
                    </div>`).join('') : '<p class="col-span-full text-center py-20 text-slate-400 italic">Nenhuma foto na galeria.</p>';
                lucide.createIcons();
            } catch (e) { notify("Erro ao conectar", "error"); }
        }

        async function doUpload() {
            const input = document.getElementById('fileInput');
            const btn = document.getElementById('upBtn');
            if(!input.files[0]) return notify("Escolha uma foto primeiro", "error");
            btn.disabled = true;
            btn.innerText = "Subindo...";
            const formData = new FormData();
            formData.append('image', input.files[0]);
            const res = await fetch('/api/upload', {
                method: 'POST',
                headers: {'x-app-password': localStorage.getItem('planeta_auth')},
                body: formData
            });
            if (res.ok) {
                notify("Foto adicionada!");
                input.value = "";
                loadImages();
            } else { notify("Erro no upload", "error"); }
            btn.disabled = false;
            btn.innerHTML = '<i data-lucide="upload-cloud"></i> Subir Foto';
            lucide.createIcons();
        }

        function copyURL(url) {
            navigator.clipboard.writeText(url);
            notify("Link copiado!");
        }

        function askDelete(name) {
            document.getElementById('modalText').innerText = `Deseja apagar a foto ${name}?`;
            document.getElementById('confirmBtn').onclick = () => finishDelete(name);
            document.getElementById('modal').classList.remove('hidden');
        }

        async function finishDelete(name) {
            closeModal('modal');
            const res = await fetch('/api/images/' + encodeURIComponent(name), {
                method: 'DELETE',
                headers: {'x-app-password': localStorage.getItem('planeta_auth')}
            });
            if (res.ok) { notify("Foto removida"); loadImages(); }
        }

        window.onload = () => {
            if (localStorage.getItem('planeta_auth')) showMain();
            lucide.createIcons();
        };
    </script>
</body>
</html>
    """)

@app.route("/api/images", methods=["GET"])
def list_images():
    try:
        files = supabase.storage.from_(BUCKET_NAME).list()
        images = []
        for f in files:
            if f['name'] == '.emptyFolderPlaceholder': continue
            res = supabase.storage.from_(BUCKET_NAME).get_public_url(f['name'])
            public_url = res if isinstance(res, str) else (res.public_url if hasattr(res, 'public_url') else res.get('publicURL', ''))
            images.append({"name": f['name'], "url": public_url})
        return jsonify(images)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/upload", methods=["POST"])
def upload():
    file = request.files['image']
    nome_final = f"{int(time.time())}_{limpar_nome_arquivo(file.filename)}"
    try:
        supabase.storage.from_(BUCKET_NAME).upload(path=nome_final, file=file.read(), file_options={"content-type": file.content_type})
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/images/<name>", methods=["DELETE"])
def delete(name):
    try:
        supabase.storage.from_(BUCKET_NAME).remove([name])
        return jsonify({"status": "deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Importante para o Easypanel reconhecer a porta correta
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
