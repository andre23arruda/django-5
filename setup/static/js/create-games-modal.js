document.addEventListener('DOMContentLoaded', function() {
    const gamesButton = document.getElementById('create-games')
    const cancelButton = document.getElementById('games-cancel')
    const gamesDialog = document.getElementById('games-dialog')

    if (gamesButton && cancelButton && gamesDialog) {
        gamesButton.addEventListener('click', function () {
            gamesDialog.showModal()
        })

        cancelButton.addEventListener('click', function () {
            gamesDialog.close()
        })

        const jogosTab = document.getElementById('jogos-tab');
        gamesButton.style.maxWidth = '100px';
        gamesButton.style.position = 'absolute';
        gamesButton.style.top = '10px';
        gamesButton.style.right = '20px';
        jogosTab.appendChild(gamesButton);
    }
})
