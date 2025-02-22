document.addEventListener('DOMContentLoaded', function() {
    const pageLoader = document.querySelector('.page-loader-wrapper')
    if (pageLoader) {
        pageLoader.style.opacity = 0
        pageLoader.style.zIndex = 0
    }
})
