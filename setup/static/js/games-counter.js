document.addEventListener('DOMContentLoaded', function() {
    const jogosInline = document.querySelector('#jogos-tab .js-inline-admin-formset.inline-group')
    const jogoInlineGroup = document.querySelector('#jogo_set-group');
    if (!jogoInlineGroup) return;

    // Coleta dados dos jogos
    const jogosRows = jogoInlineGroup.querySelectorAll('.form-row:not(.add-row)');
    const totalJogos = jogosRows.length;
    let jogosConcluidos = 0;
    let jogosPendentes = 0;

    // Conta jogos concluídos
    jogosRows.forEach(row => {
        const concluidoCheckbox = row.querySelector('select[id*="-concluido"]');
        if (concluidoCheckbox && concluidoCheckbox.value === 'C') {
            jogosConcluidos++;
        }

        const concluidoText = row.querySelector('.field-concluido p');
        if (concluidoText && concluidoText.textContent === '✅') {
            jogosConcluidos++;
        }
    });
    jogosPendentes = totalJogos - jogosConcluidos;

    if (jogosInline) {
        const html = jogosInline.innerHTML
        jogosInline.innerHTML = `
            <div class="row mx-2">
                <div class="col-4 text-center text-bold">Jogos: ${totalJogos}</div>
                <div class="col-4 text-center text-bold">Concluídos: ${jogosConcluidos}</div>
                <div class="col-4 text-center text-bold">Pendentes: ${jogosPendentes}</div>
            </div>
        ` + html
    }
})
