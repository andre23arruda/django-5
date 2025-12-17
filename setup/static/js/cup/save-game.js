(function() {
    'use strict';

    // Função para extrair o índice do jogo do name do input
    function getJogoIndex(element) {
        const name = element.name || element.getAttribute('name');
        const match = name.match(/jogo_set-(\d+)-/);
        return match ? match[1] : null;
    }

    // Função para obter o ID do jogo
    function getJogoId(index) {
        // Procura por um input hidden com o ID do jogo
        const idInput = document.querySelector(`input[name="jogo_set-${index}-id"]`);
        return idInput ? idInput.value : null;
    }

    // Função para obter os dados do jogo
    function getJogoData(index) {
        const statusSelect = document.querySelector(`select[name="jogo_set-${index}-concluido"]`);
        const pontosDupla1Input = document.querySelector(`input[name="jogo_set-${index}-pontos_dupla1"]`);
        const pontosDupla2Input = document.querySelector(`input[name="jogo_set-${index}-pontos_dupla2"]`);

        if (!statusSelect) return null;

        return {
            status: statusSelect.value,
            pontos_dupla1: pontosDupla1Input ? pontosDupla1Input.value : null,
            pontos_dupla2: pontosDupla2Input ? pontosDupla2Input.value : null
        };
    }

    // Função para salvar o jogo via AJAX
    function autoSaveJogo(jogoId, data, rowElement) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Mostrar indicador de carregamento
        showSavingIndicator(rowElement);

        fetch(`/torneio/${jogoId}/save-game/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                showSuccessIndicator(rowElement);
            } else {
                showErrorIndicator(rowElement, result.error || 'Erro ao salvar');
            }
            updateCounter();
        })
        .catch(error => {
            console.error('Erro:', error);
            showErrorIndicator(rowElement, 'Erro na comunicação com o servidor');
        });
    }

    // Função para mostrar indicador de salvamento
    function showSavingIndicator(rowElement) {
        const statusCell = rowElement.querySelector('.field-concluido');
        if (!statusCell) return;

        removeIndicators(statusCell);

        const indicator = document.createElement('span');
        indicator.className = 'auto-save-indicator saving';
        indicator.innerHTML = '⏳ Salvando...';
        indicator.style.position = 'absolute'
        indicator.style.right = '10%'
        statusCell.appendChild(indicator);
    }

    // Função para mostrar sucesso
    function showSuccessIndicator(rowElement) {
        const statusCell = rowElement.querySelector('.field-concluido');
        if (!statusCell) return;

        removeIndicators(statusCell);

        const indicator = document.createElement('span');
        indicator.className = 'auto-save-indicator success';
        indicator.innerHTML = '✓ Salvo';
        indicator.style.position = 'absolute'
        indicator.style.right = '10%'
        statusCell.appendChild(indicator);

        // Remover após 3 segundos
        setTimeout(() => {
            indicator.remove();
        }, 3000);
    }

    // Função para mostrar erro
    function showErrorIndicator(rowElement, message) {
        const statusCell = rowElement.querySelector('.field-concluido');
        if (!statusCell) return;

        removeIndicators(statusCell);

        const indicator = document.createElement('span');
        indicator.className = 'auto-save-indicator error';
        indicator.innerHTML = `✗ ${message}`;
        indicator.title = message;
        indicator.style.position = 'absolute'
        indicator.style.right = '10%'
        statusCell.appendChild(indicator);

        // Remover após 5 segundos
        setTimeout(() => {
            indicator.remove();
        }, 5000);
    }

    function updateCounter() {
        const allStatusSelects = document.querySelectorAll('select[name*="jogo_set-"][name*="-concluido"]');
        let pendentesCount = 0;
        let concluidosCount = 0;

        allStatusSelects.forEach(select => {
            if (select.value !== 'C') {
                pendentesCount++;
            } else {
                concluidosCount++;
            }
        });

        // Atualizar o texto no elemento
        const pendentesElement = document.getElementById('text-pendentes');
        if (pendentesElement) {
            pendentesElement.textContent = pendentesCount;
        }
        const concluidosElement = document.getElementById('text-concluidos');
        if (concluidosElement) {
            concluidosElement.textContent = concluidosCount;
        }
    }

    // Função para remover indicadores existentes
    function removeIndicators(cell) {
        const existingIndicators = cell.querySelectorAll('.auto-save-indicator');
        existingIndicators.forEach(ind => ind.remove());
    }

    // Função para encontrar a linha (tr) do elemento
    function findRow(element) {
        let current = element;
        while (current && current.tagName !== 'TR') {
            current = current.parentElement;
        }
        return current;
    }

    // Handler para mudança no select de status
    function handleStatusChange(event) {
        const select = event.target;
        const status = select.value;

        // Só salva se for 'A' (andamento) ou 'C' (concluído)
        // if (status !== 'A' && status !== 'C') {
        //     return;
        // }

        const index = getJogoIndex(select);
        if (!index) return;

        const jogoId = getJogoId(index);
        if (!jogoId) {
            console.warn('ID do jogo não encontrado');
            return;
        }

        const data = getJogoData(index);
        if (!data) return;

        const row = findRow(select);
        autoSaveJogo(jogoId, data, row);
    }

    // Handler para mudança nos inputs de pontuação
    function handlePontosChange(event) {
        const input = event.target;
        const index = getJogoIndex(input);
        if (!index) return;

        // Verifica se o status é 'A' ou 'C'
        const statusSelect = document.querySelector(`select[name="jogo_set-${index}-concluido"]`);
        if (!statusSelect) return;

        // const status = statusSelect.value;
        // if (status !== 'A' && status !== 'C') {
        //     return;
        // }

        const jogoId = getJogoId(index);
        if (!jogoId) return;

        const data = getJogoData(index);
        if (!data) return;

        const row = findRow(input);

        // Debounce: aguarda 1 segundo após a última digitação
        clearTimeout(input.saveTimeout);
        input.saveTimeout = setTimeout(() => {
            autoSaveJogo(jogoId, data, row);
        }, 1000);
    }

    // Inicializar quando DOM estiver pronto
    function init() {
        // Observar mudanças nos selects de status
        document.addEventListener('change', function(e) {
            if (e.target.matches('select[name*="jogo_set-"][name*="-concluido"]')) {
                handleStatusChange(e);
            }
        });

        // Observar mudanças nos inputs de pontuação
        // document.addEventListener('input', function(e) {
        //     if (e.target.matches('input[name*="jogo_set-"][name*="-pontos_dupla"]')) {
        //         handlePontosChange(e);
        //     }
        // });

        // Para Select2 (se estiver usando)
        document.addEventListener('DOMContentLoaded', function() {
            // Esperar o Select2 inicializar
            setTimeout(() => {
                jQuery(document).on('select2:select', function(e) {
                    const target = e.target;
                    if (target && target.name && target.name.includes('concluido')) {
                        handleStatusChange({ target: target });
                    }
                });
            }, 500);
        });
    }

    // Inicializar
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();