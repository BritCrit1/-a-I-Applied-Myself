(() => {
    const shell = document.querySelector("[data-notebook]");
    if (!shell) return;

    const sheets = Array.from(shell.querySelectorAll("[data-sheet]"));
    const dots = shell.querySelector("[data-sheet-dots]");
    const prevButton = shell.querySelector("[data-prev-sheet]");
    const nextButton = shell.querySelector("[data-next-sheet]");
    const homeButton = shell.querySelector("[data-go-home]");
    const prevLabel = shell.querySelector("[data-prev-label]");
    const nextLabel = shell.querySelector("[data-next-label]");
    const labels = [
        "Dashboard",
        "Resume",
        "Search",
        "Jobs",
        "Applications",
        "Activity",
        "Messages",
        "Follow-Ups",
        "Settings",
    ];
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const state = {
        activeSheet: 0,
        previousSheet: 0,
        direction: 1,
        isAnimating: false,
    };

    function renderDots() {
        dots.replaceChildren();
        sheets.forEach((_, index) => {
            const dot = document.createElement("button");
            dot.type = "button";
            dot.setAttribute("aria-label", `Go to ${labels[index]}`);
            dot.addEventListener("click", () => goToSheet(index));
            dots.append(dot);
        });
    }

    function updateControls() {
        sheets.forEach((sheet, index) => {
            const isActive = index === state.activeSheet;
            sheet.setAttribute("aria-hidden", isActive ? "false" : "true");
            sheet.inert = !isActive;
        });
        const dotButtons = Array.from(dots.querySelectorAll("button"));
        dotButtons.forEach((dot, index) => {
            dot.setAttribute("aria-current", index === state.activeSheet ? "true" : "false");
        });
        prevButton.disabled = state.activeSheet === 0 || state.isAnimating;
        nextButton.disabled = state.activeSheet === sheets.length - 1 || state.isAnimating;
        homeButton.disabled = state.activeSheet === 0 || state.isAnimating;
        prevLabel.textContent = labels[Math.max(0, state.activeSheet - 1)];
        nextLabel.textContent = labels[Math.min(sheets.length - 1, state.activeSheet + 1)];
    }

    function clearSheetClasses(sheet) {
        sheet.classList.remove("is-active", "is-leaving-next", "is-leaving-prev", "is-entering-next", "is-entering-prev");
    }

    function goToSheet(index) {
        if (index === state.activeSheet || state.isAnimating || index < 0 || index >= sheets.length) return;

        const current = sheets[state.activeSheet];
        const next = sheets[index];
        state.previousSheet = state.activeSheet;
        state.direction = index > state.activeSheet ? 1 : -1;
        state.activeSheet = index;
        state.isAnimating = true;

        updateControls();
        sheets.forEach(clearSheetClasses);
        next.classList.add("is-active", state.direction > 0 ? "is-entering-next" : "is-entering-prev");
        current.classList.add(state.direction > 0 ? "is-leaving-next" : "is-leaving-prev");

        requestAnimationFrame(() => {
            next.classList.remove("is-entering-next", "is-entering-prev");
        });

        window.setTimeout(() => {
            sheets.forEach(clearSheetClasses);
            next.classList.add("is-active");
            state.isAnimating = false;
            updateControls();
        }, prefersReducedMotion ? 20 : 520);
    }

    function nextSheet() {
        goToSheet(state.activeSheet + 1);
    }

    function previousSheet() {
        goToSheet(state.activeSheet - 1);
    }

    function goHome() {
        goToSheet(0);
    }

    shell.querySelectorAll("[data-go-sheet]").forEach((button) => {
        button.addEventListener("click", () => goToSheet(Number(button.dataset.goSheet)));
    });
    prevButton.addEventListener("click", previousSheet);
    nextButton.addEventListener("click", nextSheet);
    homeButton.addEventListener("click", goHome);

    document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowRight") nextSheet();
        if (event.key === "ArrowLeft") previousSheet();
        if (event.key === "Home") goHome();
    });

    let pointerStartX = null;
    let pointerStartY = null;

    shell.addEventListener("pointerdown", (event) => {
        pointerStartX = event.clientX;
        pointerStartY = event.clientY;
    });

    shell.addEventListener("pointerup", (event) => {
        if (pointerStartX === null || pointerStartY === null) return;
        const deltaX = event.clientX - pointerStartX;
        const deltaY = event.clientY - pointerStartY;
        pointerStartX = null;
        pointerStartY = null;
        if (Math.abs(deltaX) < 60 || Math.abs(deltaX) < Math.abs(deltaY)) return;
        if (deltaX < 0) nextSheet();
        else previousSheet();
    });

    shell.addEventListener(
        "wheel",
        (event) => {
            if (Math.abs(event.deltaX) < 40 || Math.abs(event.deltaX) < Math.abs(event.deltaY)) return;
            event.preventDefault();
            if (event.deltaX > 0) nextSheet();
            else previousSheet();
        },
        { passive: false },
    );

    renderDots();
    updateControls();
})();
