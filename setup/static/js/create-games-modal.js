document.addEventListener('DOMContentLoaded', function() {
    const hidePhase = document.getElementById('hidePhase');
    if (hidePhase) {
        const table = document.querySelector('#jogos-tab table');
        if (table) {
            table.classList.add('hide-phase');
        }
    }

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

    const nextStage = document.getElementById('nextStage');
    if (nextStage) {
        nextStage.style.maxWidth = '100px';
        nextStage.style.float = 'right';
        nextStage.style.marginBottom = '10px';
        const jogoSetGroup = document.getElementById('jogo_set-group');
        jogoSetGroup.appendChild(nextStage);
    }
})
