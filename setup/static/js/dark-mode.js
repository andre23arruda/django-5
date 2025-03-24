const darkModeToggle = document.querySelector('#darkmode-toggle')
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
        const darkMode = !getDarkMode()
        applyDarkMode(darkMode)
        changeIcon(darkMode)
        setDarkMode()
    })

    changeIcon(darkMode)
}
