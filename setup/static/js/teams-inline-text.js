document.addEventListener('DOMContentLoaded', function() {
    const duplasInline = document.querySelector('#duplas-group.js-inline-admin-formset.inline-group')
    const isActive = document.querySelector('#id_ativo').checked
    if (duplasInline && isActive) {
        const html = duplasInline.innerHTML
        duplasInline.innerHTML = '<h6 class="text-center mt-1">Verifique se o jogador já está cadastrado no sistema.</h6>' + html
    }
})
