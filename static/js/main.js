document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Prevent top/bottom rubber-band overscroll on macOS/iOS.
    const scrollRoot = document.scrollingElement || document.documentElement;

    function isVerticallyScrollable(element) {
        if (!(element instanceof Element)) {
            return false;
        }
        const style = window.getComputedStyle(element);
        const overflowY = style.overflowY;
        if (!/(auto|scroll|overlay)/.test(overflowY)) {
            return false;
        }
        return element.scrollHeight > element.clientHeight + 1;
    }

    function getScrollableAncestors(target) {
        const ancestors = [];
        let node = target instanceof Element ? target : null;

        while (node) {
            if (isVerticallyScrollable(node)) {
                ancestors.push(node);
            }
            node = node.parentElement;
        }

        if (scrollRoot && !ancestors.includes(scrollRoot)) {
            ancestors.push(scrollRoot);
        }

        return ancestors;
    }

    function canScrollInDirection(deltaY, ancestors) {
        if (deltaY === 0) {
            return true;
        }
        if (deltaY < 0) {
            return ancestors.some(function(element) {
                return element.scrollTop > 0;
            });
        }
        return ancestors.some(function(element) {
            return element.scrollTop + element.clientHeight < element.scrollHeight - 1;
        });
    }

    window.addEventListener('wheel', function(event) {
        if (event.ctrlKey) {
            return;
        }
        const ancestors = getScrollableAncestors(event.target);
        if (!canScrollInDirection(event.deltaY, ancestors)) {
            event.preventDefault();
        }
    }, { passive: false });

    let touchStartY = null;

    window.addEventListener('touchstart', function(event) {
        if (event.touches.length !== 1) {
            touchStartY = null;
            return;
        }
        touchStartY = event.touches[0].clientY;
    }, { passive: true });

    window.addEventListener('touchmove', function(event) {
        if (touchStartY === null || event.touches.length !== 1) {
            return;
        }
        const currentY = event.touches[0].clientY;
        const deltaY = touchStartY - currentY;
        const ancestors = getScrollableAncestors(event.target);
        if (!canScrollInDirection(deltaY, ancestors)) {
            event.preventDefault();
        }
    }, { passive: false });

    window.addEventListener('touchend', function() {
        touchStartY = null;
    }, { passive: true });
});
