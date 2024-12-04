document.addEventListener('DOMContentLoaded', function() {
    var updateButton = document.getElementById('create-games');
    var cancelButton = document.getElementById('games-cancel');
    var gamesDialog = document.getElementById('games-dialog');

    updateButton.addEventListener('click', function () {
        gamesDialog.showModal();
    });

    cancelButton.addEventListener('click', function () {
        gamesDialog.close();
    });
})
