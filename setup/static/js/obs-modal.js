// static/js/obs-modal.js

(function() {
    'use strict';

    let dialog;
    let textarea;

    // Criar dialog HTML
    function createDialog() {
        const dialogHtml = `
            <dialog id="obs-dialog" class="obs-dialog" style="border: 1px solid gray; border-radius: 10px; padding: 20px;">
                <div class="obs-dialog-content">
                    <section class="obs-dialog-header text-center">
                        <h4>Observações do Jogo</h4>
                    </section>

                    <div class="obs-dialog-body">
                        <textarea
                            id="obs-textarea"
                            rows="5"
                            placeholder="Digite as observações do jogo (Tie break 7/1, WO, não ocorreu, etc.)"
                        />
                    </div>

                    <div style="display: flex; justify-content: space-between; margin-top: 20px;">
                        <button type="button" class="obs-dialog-cancel button btn btn-secondary btn-sm">Cancelar</button>
                        <button type="button" class="obs-dialog-save button default btn btn-primary btn-sm">Salvar</button>
                    </div>
                </div>
            </dialog>
        `;

        document.body.insertAdjacentHTML('beforeend', dialogHtml);
        dialog = document.getElementById('obs-dialog');
        textarea = document.getElementById('obs-textarea');
    }

    // Abrir dialog
    function openDialog(jogoId, currentObs) {
        textarea.value = currentObs || '';
        textarea.dataset.jogoId = jogoId;

        dialog.showModal();
        textarea.focus();
    }

    // Fechar dialog
    function closeDialog() {
        dialog.close();
    }

    // Salvar observação
    function saveObservation() {
        const jogoId = textarea.dataset.jogoId;
        const obs = textarea.value.trim();
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        fetch(`/torneio-v2/${jogoId}/save-obs/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ obs: obs })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Atualizar botão
                const btn = document.querySelector(`button[data-jogo-id="${jogoId}"]`);
                btn.dataset.obs = obs;
                btn.title = obs || 'Adicionar observação';

                if (obs) {
                    btn.classList.add('has-obs');
                } else {
                    btn.classList.remove('has-obs');
                }

                closeDialog();

                // Mostrar mensagem de sucesso
                const messages = document.querySelector('.messagelist');
                const messageHTML = `
                    <div class="alert alert-info alert-dismissible">
                        <button type="button" class="close" data-dismiss="alert" aria-hidden="true">×</button>
                        <i class="icon fa fa-info"></i>
                        Observação salva com sucesso!
                    </div>
                `
                if (messages) {
                    messages.innerHTML = messageHTML;
                } else {
                    // Criar messagelist se não existir
                    const content = document.querySelector('#content');
                    if (content) {
                        content.insertAdjacentHTML('afterbegin', messageHTML);
                    }
                }
            } else {
                alert('Erro ao salvar observação');
            }
        })
        .catch(error => {
            console.error('Erro:', error);
            alert('Erro ao salvar observação');
        });
    }

    // Inicializar quando DOM estiver pronto
    document.addEventListener('DOMContentLoaded', function() {
        createDialog();

        // Event listeners
        document.addEventListener('click', function(e) {
            // Abrir dialog
            if (e.target.classList.contains('obs-modal-btn')) {
                e.preventDefault();
                const jogoId = e.target.dataset.jogoId;
                const currentObs = e.target.dataset.obs;
                openDialog(jogoId, currentObs);
            }

            // Fechar dialog
            if (e.target.classList.contains('obs-dialog-close') ||
                e.target.classList.contains('obs-dialog-cancel')) {
                closeDialog();
            }

            // Salvar
            if (e.target.classList.contains('obs-dialog-save')) {
                saveObservation();
            }
        });

        // Fechar ao clicar no backdrop
        dialog.addEventListener('click', function(e) {
            if (e.target === dialog) {
                closeDialog();
            }
        });
    });
})();