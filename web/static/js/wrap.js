
var textFadeIn = anime({
    targets: '.text',
    opacity: 1,
    easing: 'easeInOutQuad',
    autoplay: false
})
document.onscroll = function() {
    textFadeIn.seek(textFadeIn.duration * Reveal.getProgress());
}