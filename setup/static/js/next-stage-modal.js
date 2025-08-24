document.addEventListener('DOMContentLoaded', function() {
    const nextStageButton = document.getElementById('nextStage')
    const cancelButton = document.getElementById('stage-cancel')
    const tournamentDialog = document.getElementById('stage-dialog')

    if (nextStageButton) {
        nextStageButton.style.maxWidth = '100px';
        nextStageButton.style.float = 'right';
        const jogosTab = document.getElementById('jogos-tab');
        jogosTab.appendChild(nextStageButton);

        nextStageButton.addEventListener('click', function () {
            tournamentDialog.showModal()
        })

        cancelButton.addEventListener('click', function () {
            tournamentDialog.close()
        })
    }
})
