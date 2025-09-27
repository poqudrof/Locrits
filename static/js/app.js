/**
 * DEPRECATED: This JavaScript file is deprecated and will be replaced by React components.
 * Date: 2025-09-26
 * Migration: Frontend is being rebuilt with React + TypeScript
 *
 * JavaScript principal pour l'interface web Locrit
 */

// Utilitaires généraux
const Utils = {
    // Debounce function pour limiter les appels
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Formatter une date
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString.slice(0, 19); // Fallback
        }
    },

    // Afficher une notification
    showNotification(message, type = 'info') {
        // Créer un élément de notification
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 2000;
            max-width: 400px;
            opacity: 0;
            transform: translateX(100%);
            transition: all 0.3s ease;
        `;
        notification.textContent = message;

        // Ajouter au DOM
        document.body.appendChild(notification);

        // Animation d'entrée
        setTimeout(() => {
            notification.style.opacity = '1';
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Suppression automatique après 5 secondes
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 5000);
    },

    // Faire une requête API
    async apiRequest(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            // Essayer de parser en JSON, sinon retourner le texte
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error('Erreur API:', error);
            throw error;
        }
    }
};

// Gestion des formulaires
class FormHandler {
    constructor() {
        this.initializeFormValidation();
        this.initializeFormSubmission();
    }

    initializeFormValidation() {
        // Validation en temps réel des champs
        document.querySelectorAll('input[required], textarea[required]').forEach(field => {
            field.addEventListener('blur', () => this.validateField(field));
            field.addEventListener('input', Utils.debounce(() => this.validateField(field), 500));
        });
    }

    validateField(field) {
        const isValid = field.checkValidity();
        const errorClass = 'is-invalid';

        if (isValid) {
            field.classList.remove(errorClass);
        } else {
            field.classList.add(errorClass);
        }

        return isValid;
    }

    initializeFormSubmission() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e, form));
        });
    }

    handleFormSubmit(event, form) {
        // Valider tous les champs requis
        const requiredFields = form.querySelectorAll('input[required], textarea[required]');
        let isFormValid = true;

        requiredFields.forEach(field => {
            if (!this.validateField(field)) {
                isFormValid = false;
            }
        });

        if (!isFormValid) {
            event.preventDefault();
            Utils.showNotification('Veuillez corriger les erreurs dans le formulaire.', 'error');
            return;
        }

        // Désactiver le bouton de soumission pour éviter les doubles soumissions
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '⏳ En cours...';

            // Réactiver le bouton après un délai si la page ne se recharge pas
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
            }, 10000);
        }
    }
}

// Gestion des Locrits
class LocritManager {
    constructor() {
        this.initializeToggleButtons();
        this.initializeDeleteButtons();
    }

    initializeToggleButtons() {
        document.querySelectorAll('.toggle-locrit').forEach(button => {
            button.addEventListener('click', (e) => this.toggleLocrit(e, button));
        });
    }

    async toggleLocrit(event, button) {
        event.preventDefault();

        const locritName = button.dataset.locrit;
        if (!locritName) return;

        const originalContent = button.innerHTML;
        const originalDisabled = button.disabled;

        try {
            button.disabled = true;
            button.innerHTML = '⏳';

            const result = await Utils.apiRequest(`/locrits/${encodeURIComponent(locritName)}/toggle`, {
                method: 'POST'
            });

            if (result.success) {
                Utils.showNotification(result.message, 'success');
                // Recharger la page pour mettre à jour l'affichage
                setTimeout(() => window.location.reload(), 1000);
            } else {
                throw new Error(result.error || 'Erreur inconnue');
            }
        } catch (error) {
            Utils.showNotification(`Erreur: ${error.message}`, 'error');
            button.innerHTML = originalContent;
            button.disabled = originalDisabled;
        }
    }

    initializeDeleteButtons() {
        document.querySelectorAll('.delete-locrit').forEach(button => {
            button.addEventListener('click', (e) => this.confirmDelete(e, button));
        });
    }

    confirmDelete(event, button) {
        event.preventDefault();

        const locritName = button.dataset.locrit;
        if (!locritName) return;

        if (confirm(`Êtes-vous sûr de vouloir supprimer le Locrit "${locritName}" ?\n\nCette action est irréversible.`)) {
            // Créer et soumettre un formulaire de suppression
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/locrits/${encodeURIComponent(locritName)}/delete`;
            document.body.appendChild(form);
            form.submit();
        }
    }
}

// Gestion des thèmes
class ThemeManager {
    constructor() {
        this.initializeTheme();
    }

    initializeTheme() {
        const savedTheme = localStorage.getItem('locrit-theme');
        if (savedTheme) {
            this.applyTheme(savedTheme);
        }
    }

    applyTheme(theme) {
        document.body.setAttribute('data-theme', theme);
        localStorage.setItem('locrit-theme', theme);
    }

    toggleTheme() {
        const currentTheme = document.body.getAttribute('data-theme') || 'dark';
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        Utils.showNotification(`Thème changé vers: ${newTheme}`, 'info');
    }
}

// Auto-rafraîchissement des données
class AutoRefresh {
    constructor(interval = 30000) { // 30 secondes par défaut
        this.interval = interval;
        this.timer = null;
        this.isActive = false;
    }

    start() {
        if (this.isActive) return;

        this.isActive = true;
        this.timer = setInterval(() => {
            this.refreshData();
        }, this.interval);
    }

    stop() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
        this.isActive = false;
    }

    async refreshData() {
        // Actualiser seulement si l'utilisateur est sur la page
        if (document.hidden) return;

        try {
            // Ici on pourrait faire des requêtes AJAX pour mettre à jour les données
            // Pour l'instant, on log juste l'activité
            console.log('Auto-refresh triggered at', new Date().toLocaleTimeString());
        } catch (error) {
            console.error('Erreur lors du rafraîchissement:', error);
        }
    }
}

// Gestion des raccourcis clavier
class KeyboardShortcuts {
    constructor() {
        this.initializeShortcuts();
    }

    initializeShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K pour la recherche rapide
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.focusSearch();
            }

            // Échap pour fermer les modales
            if (e.key === 'Escape') {
                this.closeModals();
            }

            // Ctrl/Cmd + Enter pour soumettre les formulaires
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                this.submitCurrentForm();
            }
        });
    }

    focusSearch() {
        const searchInput = document.querySelector('input[type="search"], input[placeholder*="recherche" i]');
        if (searchInput) {
            searchInput.focus();
        }
    }

    closeModals() {
        // Fermer tous les modales visibles
        document.querySelectorAll('[id*="Modal"]').forEach(modal => {
            if (modal.style.display !== 'none') {
                modal.style.display = 'none';
            }
        });
    }

    submitCurrentForm() {
        const activeElement = document.activeElement;
        if (activeElement && activeElement.form) {
            // Vérifier si on est dans un textarea (on ne veut pas soumettre automatiquement)
            if (activeElement.tagName.toLowerCase() !== 'textarea') {
                const submitBtn = activeElement.form.querySelector('button[type="submit"]');
                if (submitBtn && !submitBtn.disabled) {
                    submitBtn.click();
                }
            }
        }
    }
}

// Initialisation de l'application
class LocritApp {
    constructor() {
        this.formHandler = new FormHandler();
        this.locritManager = new LocritManager();
        this.themeManager = new ThemeManager();
        this.autoRefresh = new AutoRefresh();
        this.keyboardShortcuts = new KeyboardShortcuts();

        this.initialize();
    }

    initialize() {
        // Initialiser l'auto-rafraîchissement sur les pages de liste
        if (window.location.pathname.includes('/locrits') || window.location.pathname === '/dashboard') {
            this.autoRefresh.start();
        }

        // Gérer la visibilité de la page pour l'auto-rafraîchissement
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.autoRefresh.stop();
            } else {
                this.autoRefresh.start();
            }
        });

        // Ajouter des indicateurs de chargement
        this.addLoadingIndicators();

        console.log('🏠 Locrit Web App initialized');
    }

    addLoadingIndicators() {
        // Ajouter un indicateur de chargement pour les liens de navigation
        document.querySelectorAll('a[href^="/"]').forEach(link => {
            link.addEventListener('click', function() {
                if (!this.target || this.target === '_self') {
                    // Ajouter un petit délai pour permettre à l'utilisateur de voir le feedback
                    setTimeout(() => {
                        document.body.style.cursor = 'wait';
                    }, 100);
                }
            });
        });
    }
}

// Démarrage de l'application quand le DOM est prêt
document.addEventListener('DOMContentLoaded', () => {
    window.LocritApp = new LocritApp();
});

// Export des utilitaires pour utilisation globale
window.Utils = Utils;