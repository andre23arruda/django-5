document.addEventListener('DOMContentLoaded', function() {
    const updateButton = document.getElementById('finish-tournament')
    const cancelButton = document.getElementById('tournament-cancel')
    const tournamentDialog = document.getElementById('tournament-dialog')

    if (updateButton) {
        updateButton.addEventListener('click', function () {
            tournamentDialog.showModal()
        })

        cancelButton.addEventListener('click', function () {
            tournamentDialog.close()
        })
    }
})
