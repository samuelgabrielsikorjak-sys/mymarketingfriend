const forms = document.querySelectorAll(".ai-action");

forms.forEach(function(form){
    form.addEventListener("submit",function(){
        const button = form.querySelector("button");
        button.textContent = "Loading"
        button.disabled = true;
    });
});

const statusSelect = document.querySelector("select[name='status']");

if (statusSelect) {
    statusSelect.addEventListener("change", function(){
        statusSelect.className = "status-badge status-" + statusSelect.value;
    });
}

function parseEmail(raw) {
    const match = raw.match(/^\s*Subject:\s*(.*?)\r?\n+([\s\S]*)$/i);
    if (match) {
        return { subject: match[1].trim(), body: match[2].trim() };
    }
    return { subject: "", body: raw.trim() };
}

function flashCopied(button) {
    const originalText = button.textContent;
    button.textContent = "Copied!";
    button.classList.add("copied");
    button.disabled = true;
    setTimeout(function () {
        button.textContent = originalText;
        button.classList.remove("copied");
        button.disabled = false;
    }, 1500);
}

document.querySelectorAll("[data-email-preview]").forEach(function (preview) {
    const raw = preview.querySelector(".email-raw").value;
    const { subject, body } = parseEmail(raw);

    preview.querySelector(".email-subject-text").textContent = subject || "(no subject found)";
    preview.querySelector(".email-body-text").value = body;

    preview.querySelectorAll(".btn-copy").forEach(function (button) {
        button.addEventListener("click", function () {
            const type = button.dataset.copy;
            const textToCopy = type === "subject" ? subject : type === "body" ? body : raw;

            navigator.clipboard.writeText(textToCopy).then(function () {
                flashCopied(button);
            });
        });
    });
});