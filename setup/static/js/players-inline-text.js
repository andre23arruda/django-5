document.addEventListener('DOMContentLoaded', function() {
    const playersInline = document.querySelector('#Torneio_jogadores-group.js-inline-admin-formset.inline-group')
    const isActive = document.querySelector('#id_ativo').checked
    if (playersInline && isActive) {
        const html = playersInline.innerHTML
        playersInline.innerHTML = '<h6 class="text-center mt-1">O número de jogadores deve ser multiplo de 4</h6>' + html
    }
})
