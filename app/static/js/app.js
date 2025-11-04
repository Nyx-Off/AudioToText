class AudioToTextApp {
    constructor() {
        this.currentTaskId = null;
        this.progressInterval = null;
        this.selectedFile = null;
        this.currentFormat = 'txt';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSupportedFormats();
    }

    setupEventListeners() {
        // File input
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop
        const uploadArea = document.getElementById('uploadArea');
        uploadArea.addEventListener('dragover', (e) => this.handleDragOver(e));
        uploadArea.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        uploadArea.addEventListener('drop', (e) => this.handleFileDrop(e));

        // Form submission
        const startBtn = document.getElementById('startTranscription');
        startBtn.addEventListener('click', () => this.startTranscription());

        // Output format change
        const outputFormat = document.getElementById('outputFormat');
        outputFormat.addEventListener('change', (e) => {
            this.currentFormat = e.target.value;
        });

        // Prevent default drag behaviors
        document.addEventListener('dragover', (e) => e.preventDefault());
        document.addEventListener('drop', (e) => e.preventDefault());
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.currentTarget.classList.remove('dragover');
    }

    handleFileDrop(e) {
        e.preventDefault();
        e.currentTarget.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.processFile(files[0]);
        }
    }

    processFile(file) {
        // Validate file type
        const supportedExtensions = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        if (!supportedExtensions.includes(fileExtension)) {
            this.showToast('Format de fichier non supporté', 'error');
            return;
        }

        // Validate file size (100MB)
        const maxSize = 100 * 1024 * 1024;
        if (file.size > maxSize) {
            this.showToast('Le fichier dépasse la limite de 100MB', 'error');
            return;
        }

        this.selectedFile = file;
        this.displayFileInfo(file);
        document.getElementById('startTranscription').disabled = false;
    }

    displayFileInfo(file) {
        const fileInfo = document.getElementById('fileInfo');
        const fileName = file.name;
        const fileSize = this.formatFileSize(file.size);

        fileInfo.innerHTML = `
            <div class="file-name">${fileName}</div>
            <div class="file-size">Taille: ${fileSize}</div>
        `;
        fileInfo.classList.add('show');
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async startTranscription() {
        if (!this.selectedFile) {
            this.showToast('Veuillez sélectionner un fichier audio', 'error');
            return;
        }

        try {
            // Get form options
            const formData = new FormData();
            formData.append('file', this.selectedFile);
            formData.append('detect_speakers', document.getElementById('detectSpeakers').checked);
            formData.append('model_size', document.getElementById('modelSelect').value);
            formData.append('language', document.getElementById('languageSelect').value);
            
            // Save current format
            this.currentFormat = document.getElementById('outputFormat').value;
            formData.append('output_format', this.currentFormat);

            // Show progress section
            this.showProgressSection();

            // Start transcription
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Erreur lors du téléchargement');
            }

            const result = await response.json();
            this.currentTaskId = result.task_id;

            // Start polling for progress
            this.startProgressPolling();

        } catch (error) {
            console.error('Error starting transcription:', error);
            this.showError(error.message);
        }
    }

    showProgressSection() {
        document.querySelector('.upload-section').style.display = 'none';
        document.getElementById('progressSection').style.display = 'block';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';
        document.getElementById('taskId').textContent = '';
    }

    startProgressPolling() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        this.progressInterval = setInterval(() => {
            this.checkProgress();
        }, 2000);
    }

    async checkProgress() {
        if (!this.currentTaskId) return;

        try {
            const response = await fetch(`/status/${this.currentTaskId}`);
            if (!response.ok) {
                throw new Error('Erreur lors de la vérification du statut');
            }

            const data = await response.json();
            this.updateProgress(data);

            if (data.status === 'completed') {
                this.handleTranscriptionComplete();
            } else if (data.status === 'failed') {
                this.handleTranscriptionError(data.error);
            }

        } catch (error) {
            console.error('Error checking progress:', error);
        }
    }

    updateProgress(data) {
        const progressPercent = Math.round(data.progress * 100);
        document.getElementById('progressFill').style.width = `${progressPercent}%`;
        document.getElementById('progressText').textContent = `${progressPercent}%`;
        document.getElementById('statusMessage').textContent = data.message || '';
        document.getElementById('taskId').textContent = data.task_id;
    }

    async handleTranscriptionComplete() {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        try {
            const response = await fetch(`/result/${this.currentTaskId}`);
            if (!response.ok) {
                throw new Error('Erreur lors de la récupération du résultat');
            }

            const result = await response.json();
            this.displayResults(result);

        } catch (error) {
            console.error('Error getting result:', error);
            this.showError('Erreur lors de la récupération du résultat');
        }
    }

    displayResults(result) {
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'block';

        // Display metadata
        const metadataHtml = `
            <div class="meta-item">
                <div class="meta-label">Durée</div>
                <div class="meta-value">${this.formatDuration(result.duration)}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Interlocuteurs</div>
                <div class="meta-value">${result.num_speakers}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Langue</div>
                <div class="meta-value">${result.language ? result.language.toUpperCase() : 'Non détectée'}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Modèle</div>
                <div class="meta-value">${result.metadata.model_size}</div>
            </div>
        `;
        document.getElementById('resultsMeta').innerHTML = metadataHtml;

        // Display transcription
        const contentDiv = document.getElementById('transcriptionContent');
        if (result.segments && result.segments.length > 0) {
            let html = '';
            result.segments.forEach(segment => {
                const timestamp = this.formatTimestamp(segment.start_time);
                const speaker = segment.speaker || 'Speaker 1';
                html += `
                    <div class="speaker-segment">
                        <div class="speaker-label">${speaker}</div>
                        <div>
                            <span class="timestamp">${timestamp}</span>
                            <span class="segment-text">${segment.text}</span>
                        </div>
                    </div>
                `;
            });
            contentDiv.innerHTML = html;
        } else {
            contentDiv.textContent = result.full_text || 'Aucune transcription disponible';
        }

        this.showToast('Transcription terminée avec succès!', 'success');
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}h ${minutes}m ${secs}s`;
        } else if (minutes > 0) {
            return `${minutes}m ${secs}s`;
        } else {
            return `${secs}s`;
        }
    }

    formatTimestamp(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    handleTranscriptionError(error) {
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }
        this.showError(error || 'Une erreur est survenue pendant la transcription');
    }

    showError(message) {
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'block';
        document.getElementById('errorMessage').textContent = message;
    }

    async copyToClipboard() {
        const content = document.getElementById('transcriptionContent');
        let text = '';

        // Extract text from segments
        const segments = content.querySelectorAll('.speaker-segment');
        if (segments.length > 0) {
            segments.forEach(segment => {
                const speaker = segment.querySelector('.speaker-label').textContent;
                const timestamp = segment.querySelector('.timestamp').textContent;
                const segmentText = segment.querySelector('.segment-text').textContent;
                text += `${timestamp} ${speaker}: ${segmentText}\n`;
            });
        } else {
            text = content.textContent || content.innerText;
        }

        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Texte copié dans le presse-papiers', 'success');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            // Fallback method
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                this.showToast('Texte copié dans le presse-papiers', 'success');
            } catch (err) {
                this.showToast('Erreur lors de la copie', 'error');
            }
            document.body.removeChild(textArea);
        }
    }

    async downloadResult() {
        if (!this.currentTaskId) {
            this.showToast('Aucune transcription disponible', 'error');
            return;
        }

        try {
            // Use the current format
            const format = this.currentFormat || 'txt';
            const response = await fetch(`/download/${this.currentTaskId}?format=${format}`);

            if (!response.ok) {
                throw new Error('Erreur lors du téléchargement');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcription.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showToast('Fichier téléchargé avec succès', 'success');

        } catch (error) {
            console.error('Error downloading result:', error);
            this.showToast('Erreur lors du téléchargement', 'error');
        }
    }

    resetForm() {
        // Clear intervals
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
        }

        // Reset state
        this.currentTaskId = null;
        this.selectedFile = null;
        this.currentFormat = 'txt';

        // Reset form
        document.getElementById('fileInput').value = '';
        document.getElementById('fileInfo').classList.remove('show');
        document.getElementById('startTranscription').disabled = true;

        // Show upload section
        document.querySelector('.upload-section').style.display = 'block';
        document.getElementById('progressSection').style.display = 'none';
        document.getElementById('resultsSection').style.display = 'none';
        document.getElementById('errorSection').style.display = 'none';

        // Reset progress
        document.getElementById('progressFill').style.width = '0%';
        document.getElementById('progressText').textContent = '0%';
        document.getElementById('statusMessage').textContent = '';
    }

    showToast(message, type = 'info') {
        // Remove existing toast
        const existingToast = document.querySelector('.toast');
        if (existingToast) {
            existingToast.remove();
        }

        // Create new toast
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);

        // Remove after 3 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 3000);
    }

    async loadSupportedFormats() {
        try {
            const response = await fetch('/models');
            if (response.ok) {
                const data = await response.json();
                console.log('Available models:', data);
            }
        } catch (error) {
            console.error('Error loading models:', error);
        }
    }
}

// Global functions for HTML onclick events
function copyToClipboard() {
    if (window.app) {
        window.app.copyToClipboard();
    }
}

function downloadResult() {
    if (window.app) {
        window.app.downloadResult();
    }
}

function resetForm() {
    if (window.app) {
        window.app.resetForm();
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new AudioToTextApp();
});
