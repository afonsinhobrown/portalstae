/* static/dfec/js/editor_manuais.js - NOVO ARQUIVO */
// Editor de manuais com funcionalidades avançadas

class EditorManuais {
    constructor(options = {}) {
        this.options = {
            editorId: 'editor-conteudo',
            uploadUrl: '/api/manuais/upload-imagem/',
            saveUrl: '/api/manuais/salvar-conteudo/',
            ...options
        };

        this.init();
    }

    init() {
        this.setupEditor();
        this.setupEventListeners();
        this.setupImageLibrary();
        this.setupAutoSave();
    }

    setupEditor() {
        // Inicializar editor de texto rico
        if (typeof tinymce !== 'undefined') {
            tinymce.init({
                selector: `#${this.options.editorId}`,
                height: 500,
                menubar: 'file edit view insert format tools table help',
                plugins: [
                    'advlist', 'autolink', 'lists', 'link', 'image', 'charmap', 'preview',
                    'anchor', 'searchreplace', 'visualblocks', 'code', 'fullscreen',
                    'insertdatetime', 'media', 'table', 'code', 'help', 'wordcount'
                ],
                toolbar: 'undo redo | blocks | ' +
                    'bold italic forecolor | alignleft aligncenter ' +
                    'alignright alignjustify | bullist numlist outdent indent | ' +
                    'removeformat | help | image table',
                image_uploadtab: true,
                images_upload_handler: this.handleImageUpload.bind(this),
                content_style: 'body { font-family: Arial, sans-serif; font-size: 14px; }'
            });
        } else {
            // Fallback para textarea básico
            console.warn('TinyMCE não carregado. Usando editor básico.');
        }
    }

    setupEventListeners() {
        // Botão de inserir imagem da biblioteca
        document.getElementById('btnInserirImagem')?.addEventListener('click', () => {
            this.openImageLibrary();
        });

        // Botão de salvar capítulo
        document.getElementById('btnSalvarCapitulo')?.addEventListener('click', () => {
            this.saveChapter();
        });

        // Drag and drop para imagens
        const dropZone = document.getElementById('dropZoneImagens');
        if (dropZone) {
            dropZone.addEventListener('dragover', this.handleDragOver.bind(this));
            dropZone.addEventListener('drop', this.handleDrop.bind(this));
        }
    }

    setupImageLibrary() {
        // Carregar imagens da biblioteca
        this.loadImageLibrary();
    }

    setupAutoSave() {
        // Auto-save a cada 30 segundos
        setInterval(() => {
            if (this.hasUnsavedChanges()) {
                this.autoSave();
            }
        }, 30000);
    }

    async handleImageUpload(blobInfo, success, failure) {
        const formData = new FormData();
        formData.append('file', blobInfo.blob(), blobInfo.filename());
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
            const response = await fetch(this.options.uploadUrl, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                success(data.url);

                // Registrar no histórico
                this.logImageUpload(blobInfo.filename());
            } else {
                failure(data.error || 'Erro no upload');
            }
        } catch (error) {
            failure('Erro de conexão: ' + error.message);
        }
    }

    openImageLibrary() {
        // Abrir modal da biblioteca de imagens
        const modal = new bootstrap.Modal(document.getElementById('imageLibraryModal'));
        modal.show();

        // Carregar imagens
        this.loadImageLibrary();
    }

    async loadImageLibrary() {
        const container = document.getElementById('imageLibraryContainer');
        if (!container) return;

        try {
            const response = await fetch('/api/manuais/imagens/');
            const data = await response.json();

            container.innerHTML = '';

            data.images.forEach(image => {
                const imgElement = this.createImageThumbnail(image);
                container.appendChild(imgElement);
            });
        } catch (error) {
            console.error('Erro ao carregar biblioteca:', error);
        }
    }

    createImageThumbnail(image) {
        const div = document.createElement('div');
        div.className = 'col-md-3 col-6 mb-3';

        div.innerHTML = `
            <div class="card image-card" data-image-id="${image.id}">
                <img src="${image.thumbnail_url}" class="card-img-top" alt="${image.titulo}">
                <div class="card-body p-2">
                    <h6 class="card-title mb-1">${image.titulo}</h6>
                    <small class="text-muted">${image.descricao || ''}</small>
                    <div class="mt-2">
                        <button class="btn btn-sm btn-primary btn-inserir"
                                onclick="editorManuais.insertImage(${image.id})">
                            <i class="fas fa-plus"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-secondary btn-info"
                                onclick="editorManuais.showImageInfo(${image.id})">
                            <i class="fas fa-info"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;

        return div;
    }

    insertImage(imageId) {
        // Inserir imagem no editor
        if (typeof tinymce !== 'undefined') {
            tinymce.activeEditor.insertContent(
                `<img src="/media/manuais/imagens/${imageId}" alt="Imagem ${imageId}" style="max-width: 100%;">`
            );
        }

        // Fechar modal
        bootstrap.Modal.getInstance(document.getElementById('imageLibraryModal')).hide();
    }

    showImageInfo(imageId) {
        // Mostrar detalhes da imagem
        fetch(`/api/manuais/imagens/${imageId}/`)
            .then(response => response.json())
            .then(data => {
                // Mostrar modal com informações
                this.showModal('Informações da Imagem', this.createImageInfoHTML(data));
            });
    }

    createImageInfoHTML(image) {
        return `
            <div class="row">
                <div class="col-md-6">
                    <img src="${image.url}" class="img-fluid rounded" alt="${image.titulo}">
                </div>
                <div class="col-md-6">
                    <h5>${image.titulo}</h5>
                    <p>${image.descricao || 'Sem descrição'}</p>
                    <dl class="row">
                        <dt class="col-sm-4">Autor:</dt>
                        <dd class="col-sm-8">${image.autor || 'Desconhecido'}</dd>

                        <dt class="col-sm-4">Fonte:</dt>
                        <dd class="col-sm-8">${image.fonte || 'Não especificada'}</dd>

                        <dt class="col-sm-4">Licença:</dt>
                        <dd class="col-sm-8">${image.licenca || 'Não especificada'}</dd>

                        <dt class="col-sm-4">Dimensões:</dt>
                        <dd class="col-sm-8">${image.width} × ${image.height} px</dd>

                        <dt class="col-sm-4">Tamanho:</dt>
                        <dd class="col-sm-8">${this.formatFileSize(image.size)}</dd>
                    </dl>
                    <div class="mt-3">
                        <button class="btn btn-primary" onclick="editorManuais.insertImage(${image.id})">
                            <i class="fas fa-plus me-1"></i> Inserir no Manual
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    async saveChapter() {
        const form = document.getElementById('formCapitulo');
        if (!form) return;

        const formData = new FormData(form);

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Capítulo salvo com sucesso!');
                this.clearUnsavedChanges();
            } else {
                this.showError(data.error || 'Erro ao salvar capítulo');
            }
        } catch (error) {
            this.showError('Erro de conexão: ' + error.message);
        }
    }

    async autoSave() {
        const content = this.getEditorContent();
        const chapterId = this.getCurrentChapterId();

        if (!content || !chapterId) return;

        try {
            const response = await fetch(this.options.saveUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    chapter_id: chapterId,
                    content: content,
                    auto_save: true
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showAutoSaveIndicator();
            }
        } catch (error) {
            console.error('Erro no auto-save:', error);
        }
    }

    getEditorContent() {
        if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
            return tinymce.activeEditor.getContent();
        }

        const editor = document.getElementById(this.options.editorId);
        return editor ? editor.value : '';
    }

    getCurrentChapterId() {
        return document.querySelector('[name="capitulo_id"]')?.value ||
               document.querySelector('#formCapitulo [name="id"]')?.value;
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    }

    hasUnsavedChanges() {
        const savedContent = localStorage.getItem('editor_saved_content');
        const currentContent = this.getEditorContent();

        return savedContent !== currentContent;
    }

    clearUnsavedChanges() {
        const currentContent = this.getEditorContent();
        localStorage.setItem('editor_saved_content', currentContent);
    }

    showAutoSaveIndicator() {
        const indicator = document.getElementById('autoSaveIndicator') ||
                         this.createAutoSaveIndicator();

        indicator.textContent = 'Salvo automaticamente';
        indicator.classList.remove('d-none');

        setTimeout(() => {
            indicator.classList.add('d-none');
        }, 2000);
    }

    createAutoSaveIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'autoSaveIndicator';
        indicator.className = 'alert alert-info alert-dismissible fade show d-none';
        indicator.innerHTML = `
            <i class="fas fa-save me-2"></i>
            <span></span>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.querySelector('.content-wrapper').prepend(indicator);
        return indicator;
    }

    showSuccess(message) {
        this.showToast(message, 'success');
    }

    showError(message) {
        this.showToast(message, 'danger');
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast"></button>
            </div>
        `;

        const container = document.getElementById('toastContainer') || this.createToastContainer();
        container.appendChild(toast);

        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    handleDragOver(e) {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'copy';

        const dropZone = e.target;
        dropZone.classList.add('dragover');
    }

    async handleDrop(e) {
        e.preventDefault();
        e.stopPropagation();

        const dropZone = e.target;
        dropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length === 0) return;

        // Processar cada arquivo
        for (let file of files) {
            if (file.type.startsWith('image/')) {
                await this.uploadDroppedImage(file);
            }
        }
    }

    async uploadDroppedImage(file) {
        const formData = new FormData();
        formData.append('imagem', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        try {
            const response = await fetch('/api/manuais/upload-imagem-rapida/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Inserir automaticamente no editor
                this.insertImage(data.image_id);
            }
        } catch (error) {
            this.showError('Erro ao fazer upload da imagem: ' + error.message);
        }
    }

    logImageUpload(filename) {
        // Registrar upload no histórico
        fetch('/api/manuais/log-upload/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken()
            },
            body: JSON.stringify({
                filename: filename,
                timestamp: new Date().toISOString()
            })
        });
    }
}

// Inicializar editor quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    window.editorManuais = new EditorManuais();
});