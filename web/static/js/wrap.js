
/*var scrollPageTransition = anime({
    targets: '.scroll-page',
    opacity: 1,
    easing: 'easeInOutQuad',
    autoplay: false
})
Reveal.on('slidechanged', function(event) {
    console.log(Reveal.getProgress());
    var element = Reveal.getSlideBackground(event.indexh, event.indexv);
    scrollPageTransition.seek(scrollPageTransition.duration * element.getBoundingClientRect().top / window.innerHeight);
})*/

var scrollPageTransition = anime({
    targets: '.scroll-page',
    opacity: 1,
    easing: 'easeInOutQuad',
    autoplay: false
})
