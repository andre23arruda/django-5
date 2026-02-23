const darkModeIcons = {
    true: '<i class="fa-solid fa-moon"></i>',
    false: '<i class="fa-solid fa-circle-half-stroke"></i>'

}

function getDarkMode() {
    return JSON.parse(localStorage.getItem('darkMode')) || false
}

function setDarkMode() {
    const darkMode = !getDarkMode()
    localStorage.setItem('darkMode', darkMode)
}

function applyDarkMode(darkMode) {
    const body = document.querySelector('body')
    if (darkMode) {
        body.classList.add('theme-cyborg', 'dark-mode')
    } else {
        body.classList.remove('theme-cyborg', 'dark-mode')
    }
}

function changeIcon(darkMode) {
    const darkModeToggle = document.querySelector('#darkmode-toggle span')
    darkModeToggle.innerHTML = darkModeIcons[darkMode]
}

const darkMode = getDarkMode()
applyDarkMode(darkMode)
