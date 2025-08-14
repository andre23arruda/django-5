document.addEventListener('DOMContentLoaded', function() {
    const hidePhase = document.getElementById('hidePhase');
    if (hidePhase) {
        const table = document.querySelector('#jogos-tab table');
        if (table) {
            table.classList.add('hide-phase');
        }
    }

    const canCreateGames = document.getElementById('canCreateGames');
    const jogosTab = document.getElementById('jogos-tab');
    if (jogosTab && canCreateGames) {
        jogosTab.innerHTML += `
            <button
                id="create-games"
                type="button"
                class="btn btn-block btn-primary btn-sm mt-2"
                style="
                    position: absolute;
                    top: 10px;
                    right: 20px;
                    max-width: 100px;
                "
            >
                Gerar Jogos
            </button>
        `
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
    }
})
