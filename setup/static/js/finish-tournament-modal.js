document.addEventListener('DOMContentLoaded', function() {
    const finishButton = document.getElementById('finish-tournament')
    const cancelButton = document.getElementById('tournament-cancel')
    const tournamentDialog = document.getElementById('tournament-dialog')

    if (finishButton) {
        finishButton.addEventListener('click', function () {
            tournamentDialog.showModal()
        })

        cancelButton.addEventListener('click', function () {
            tournamentDialog.close()
        })
    }
})
