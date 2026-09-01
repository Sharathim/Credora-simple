/**
 * Credora — Academic Certificate Perceptual Verification App
 * Frontend client logic for Issuer Upload and Certificate Verification.
 */

document.addEventListener("DOMContentLoaded", () => {
    // State
    let lastIssuedCertId = localStorage.getItem("lastIssuedCertId") || "";
    let issuerFile = null;
    let verifierFile = null;
    let currentVerifyData = null;

    // Elements - Tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanels = document.querySelectorAll(".tab-panel");

    // Elements - Issuer
    const issuerForm = document.getElementById("issuer-form");
    const issuerDropZone = document.getElementById("issuer-drop-zone");
    const issuerFileInput = document.getElementById("issuer-file-input");
    const issuerDropContent = document.getElementById("issuer-drop-content");
    const issuerPreviewWrapper = document.getElementById("issuer-preview-wrapper");
    const issuerImagePreview = document.getElementById("issuer-image-preview");
    const btnIssuerClear = document.getElementById("btn-issuer-clear");
    const btnIssuerSubmit = document.getElementById("btn-issuer-submit");
    const issuerSpinner = document.getElementById("issuer-spinner");
    const issuerEmptyState = document.getElementById("issuer-empty-state");
    const issuerOutputContent = document.getElementById("issuer-output-content");
    const dispIssuerCertId = document.getElementById("disp-issuer-cert-id");
    const btnCopyCertId = document.getElementById("btn-copy-cert-id");
    const issuerQualityTable = document.getElementById("issuer-quality-table");
    const issuerCanonicalImg = document.getElementById("issuer-canonical-img");
    const btnSwitchToVerify = document.getElementById("btn-switch-to-verify");

    // Elements - Verifier
    const verifierForm = document.getElementById("verifier-form");
    const verifierCertIdInput = document.getElementById("verifier-cert-id");
    const btnFillRecentId = document.getElementById("btn-fill-recent-id");
    const verifierDropZone = document.getElementById("verifier-drop-zone");
    const verifierFileInput = document.getElementById("verifier-file-input");
    const verifierDropContent = document.getElementById("verifier-drop-content");
    const verifierPreviewWrapper = document.getElementById("verifier-preview-wrapper");
    const verifierImagePreview = document.getElementById("verifier-image-preview");
    const btnVerifierClear = document.getElementById("btn-verifier-clear");
    const thresholdSlider = document.getElementById("threshold-slider");
    const thresholdDisplay = document.getElementById("threshold-display");
    const btnVerifierSubmit = document.getElementById("btn-verifier-submit");
    const verifierSpinner = document.getElementById("verifier-spinner");
    const verifierEmptyState = document.getElementById("verifier-empty-state");
    const verifierPipelineProgress = document.getElementById("verifier-pipeline-progress");
    const verifierOutputContent = document.getElementById("verifier-output-content");
    const decisionHero = document.getElementById("decision-hero");
    const decisionIcon = document.getElementById("decision-icon");
    const decisionBadge = document.getElementById("decision-badge");
    const decisionSimScore = document.getElementById("decision-sim-score");
    const decisionSimPill = document.getElementById("decision-sim-pill");
    const decisionExplanation = document.getElementById("decision-explanation");
    const verifierQualityTable = document.getElementById("verifier-quality-table");
    const compareIssuerImg = document.getElementById("compare-issuer-img");
    const compareVerifierImg = document.getElementById("compare-verifier-img");
    const algoBreakdownGrid = document.getElementById("algo-breakdown-grid");
    const appToast = document.getElementById("app-toast");

    // Initial setup
    if (lastIssuedCertId) {
        verifierCertIdInput.value = lastIssuedCertId;
    }

    // -------------------------------------------------------------
    // Tab Navigation
    // -------------------------------------------------------------
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const target = btn.dataset.tab;
            switchTab(target);
        });
    });

    function switchTab(targetId) {
        tabBtns.forEach(b => b.classList.toggle("active", b.dataset.tab === targetId));
        tabPanels.forEach(p => p.classList.toggle("active", p.id === targetId));
    }

    if (btnSwitchToVerify) {
        btnSwitchToVerify.addEventListener("click", () => {
            switchTab("verifier-section");
        });
    }

    // -------------------------------------------------------------
    // Drag & Drop File Handlers
    // -------------------------------------------------------------
    function setupDropZone(dropZone, fileInput, dropContent, previewWrapper, imagePreview, onFileSelected) {
        dropZone.addEventListener("click", (e) => {
            if (!previewWrapper.classList.contains("hidden") && e.target.closest(".btn-clear-preview")) return;
            fileInput.click();
        });

        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                onFileSelected(fileInput.files[0]);
            }
        });

        ["dragenter", "dragover"].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.add("dragover");
            });
        });

        ["dragleave", "drop"].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.remove("dragover");
            });
        });

        dropZone.addEventListener("drop", (e) => {
            if (e.dataTransfer.files.length > 0) {
                onFileSelected(e.dataTransfer.files[0]);
            }
        });
    }

    // Issuer File Selection
    setupDropZone(issuerDropZone, issuerFileInput, issuerDropContent, issuerPreviewWrapper, issuerImagePreview, (file) => {
        issuerFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            issuerImagePreview.src = e.target.result;
            issuerDropContent.classList.add("hidden");
            issuerPreviewWrapper.classList.remove("hidden");
        };
        reader.readAsDataURL(file);
    });

    btnIssuerClear.addEventListener("click", (e) => {
        e.stopPropagation();
        issuerFile = null;
        issuerFileInput.value = "";
        issuerPreviewWrapper.classList.add("hidden");
        issuerDropContent.classList.remove("hidden");
    });

    // Verifier File Selection
    setupDropZone(verifierDropZone, verifierFileInput, verifierDropContent, verifierPreviewWrapper, verifierImagePreview, (file) => {
        verifierFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            verifierImagePreview.src = e.target.result;
            verifierDropContent.classList.add("hidden");
            verifierPreviewWrapper.classList.remove("hidden");
        };
        reader.readAsDataURL(file);
    });

    btnVerifierClear.addEventListener("click", (e) => {
        e.stopPropagation();
        verifierFile = null;
        verifierFileInput.value = "";
        verifierPreviewWrapper.classList.add("hidden");
        verifierDropContent.classList.remove("hidden");
    });

    btnFillRecentId.addEventListener("click", () => {
        if (lastIssuedCertId) {
            verifierCertIdInput.value = lastIssuedCertId;
            showToast(`Filled Certificate ID: ${lastIssuedCertId}`, "success");
        } else {
            showToast("No recently registered Certificate ID found.", "error");
        }
    });

    // Threshold Slider
    thresholdSlider.addEventListener("input", (e) => {
        const val = e.target.value;
        thresholdDisplay.innerText = `${val}%`;
        if (currentVerifyData) {
            recalculateDecision(parseFloat(val));
        }
    });

    // Copy Cert ID
    btnCopyCertId.addEventListener("click", () => {
        const text = dispIssuerCertId.innerText;
        navigator.clipboard.writeText(text).then(() => {
            showToast("Certificate ID copied to clipboard!", "success");
        });
    });

    // -------------------------------------------------------------
    // Issuer Form Submission
    // -------------------------------------------------------------
    issuerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!issuerFile) {
            showToast("Please select or drop a certificate image first.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("image", issuerFile);
        formData.append("student_name", document.getElementById("issuer-student").value.trim());
        formData.append("university", document.getElementById("issuer-univ").value.trim());
        formData.append("degree", document.getElementById("issuer-degree").value.trim());
        formData.append("issue_date", document.getElementById("issuer-date").value.trim());

        setButtonLoading(btnIssuerSubmit, issuerSpinner, true);

        try {
            const resp = await fetch("/api/issuer/upload", {
                method: "POST",
                body: formData
            });
            const data = await resp.json();

            if (resp.ok && data.success) {
                lastIssuedCertId = data.cert_id;
                localStorage.setItem("lastIssuedCertId", lastIssuedCertId);
                verifierCertIdInput.value = lastIssuedCertId;

                dispIssuerCertId.innerText = data.cert_id;
                renderQualityTable(issuerQualityTable, data.quality_report.checks);
                issuerCanonicalImg.src = data.preprocessed_image_url;

                issuerEmptyState.classList.add("hidden");
                issuerOutputContent.classList.remove("hidden");
                showToast(`Certificate registered! ID: ${data.cert_id}`, "success");
            } else {
                if (data.quality_report) {
                    renderQualityTable(issuerQualityTable, data.quality_report.checks);
                    issuerEmptyState.classList.add("hidden");
                    issuerOutputContent.classList.remove("hidden");
                    dispIssuerCertId.innerText = "REGISTRATION REJECTED";
                }
                showToast(data.message || "Registration failed quality requirements.", "error");
            }
        } catch (err) {
            showToast(`Network error: ${err.message}`, "error");
        } finally {
            setButtonLoading(btnIssuerSubmit, issuerSpinner, false);
        }
    });

    // -------------------------------------------------------------
    // Verifier Form Submission
    // -------------------------------------------------------------
    verifierForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const certId = verifierCertIdInput.value.trim();
        if (!certId) {
            showToast("Please enter a Certificate ID.", "error");
            return;
        }
        if (!verifierFile) {
            showToast("Please upload a verification photograph or scan.", "error");
            return;
        }

        const formData = new FormData();
        formData.append("cert_id", certId);
        formData.append("threshold", thresholdSlider.value);
        formData.append("image", verifierFile);

        // Staged progress animation
        verifierEmptyState.classList.add("hidden");
        verifierOutputContent.classList.add("hidden");
        verifierPipelineProgress.classList.remove("hidden");
        setButtonLoading(btnVerifierSubmit, verifierSpinner, true);

        await runPipelineAnimation();

        try {
            const resp = await fetch("/api/verifier/verify", {
                method: "POST",
                body: formData
            });
            const data = await resp.json();

            verifierPipelineProgress.classList.add("hidden");

            if (resp.ok && data.success) {
                currentVerifyData = data;
                renderVerificationResult(data);
                showToast(`Verification complete: ${data.decision}`, data.is_match ? "success" : "error");
            } else {
                currentVerifyData = null;
                if (data.quality_report) {
                    renderQualityFailure(data);
                } else {
                    showToast(data.message || "Verification failed.", "error");
                    verifierEmptyState.classList.remove("hidden");
                }
            }
        } catch (err) {
            verifierPipelineProgress.classList.add("hidden");
            showToast(`Network error: ${err.message}`, "error");
            verifierEmptyState.classList.remove("hidden");
        } finally {
            setButtonLoading(btnVerifierSubmit, verifierSpinner, false);
        }
    });

    async function runPipelineAnimation() {
        const steps = ["step-1", "step-2", "step-3", "step-4"];
        steps.forEach(id => {
            const el = document.getElementById(id);
            el.className = "step-item";
        });

        for (let i = 0; i < steps.length; i++) {
            const el = document.getElementById(steps[i]);
            el.classList.add("active");
            await new Promise(r => setTimeout(r, 220));
            el.classList.remove("active");
            el.classList.add("done");
        }
    }

    function renderVerificationResult(data) {
        verifierOutputContent.classList.remove("hidden");

        // Decision Hero
        decisionHero.className = `decision-hero ${data.is_match ? 'match' : 'mismatch'}`;
        decisionIcon.innerText = data.is_match ? "✅" : "❌";
        decisionBadge.innerText = data.decision === "MATCH" ? "CERTIFICATE MATCH" : "CERTIFICATE MISMATCH";
        decisionSimScore.innerText = `${data.similarity_percentage.toFixed(1)}%`;
        decisionSimPill.innerText = `Hamming Dist: ${data.hamming_distance} / 64`;
        decisionExplanation.innerText = data.status_text;

        // Quality table
        renderQualityTable(verifierQualityTable, data.quality_report.checks);

        // Side-by-Side Images
        compareIssuerImg.src = data.issuer_original_url;
        compareVerifierImg.src = data.verifier_processed_url;

        // Breakdown
        algoBreakdownGrid.innerHTML = "";
        Object.entries(data.hash_breakdown).forEach(([key, info]) => {
            const card = document.createElement("div");
            card.className = "algo-card";
            card.innerHTML = `
                <div class="algo-title">${info.name}</div>
                <div class="algo-score">${info.similarity.toFixed(1)}%</div>
                <div class="quality-val">Hamming Dist: ${info.hamming_dist}</div>
            `;
            algoBreakdownGrid.appendChild(card);
        });
    }

    function renderQualityFailure(data) {
        verifierOutputContent.classList.remove("hidden");
        decisionHero.className = "decision-hero mismatch";
        decisionIcon.innerText = "⛔";
        decisionBadge.innerText = "QUALITY CHECK REJECTED";
        decisionSimScore.innerText = "N/A";
        decisionSimPill.innerText = "Quality Gate Failed";
        decisionExplanation.innerText = data.message || "Uploaded image did not pass automated quality checks. Preprocessing & hashing aborted.";

        renderQualityTable(verifierQualityTable, data.quality_report.checks);
        compareIssuerImg.src = "";
        compareVerifierImg.src = "";
        showToast(data.message, "error");
    }

    function recalculateDecision(threshold) {
        if (!currentVerifyData) return;
        const sim = currentVerifyData.similarity_percentage;
        const isMatch = sim >= threshold;

        decisionHero.className = `decision-hero ${isMatch ? 'match' : 'mismatch'}`;
        decisionIcon.innerText = isMatch ? "✅" : "❌";
        decisionBadge.innerText = isMatch ? "CERTIFICATE MATCH" : "CERTIFICATE MISMATCH";
        decisionExplanation.innerText = isMatch
            ? "Certificate appears visually consistent with the issuer's original."
            : "The uploaded certificate differs significantly from the issuer's original under the current threshold.";
    }

    // -------------------------------------------------------------
    // Quality Table Generator
    // -------------------------------------------------------------
    function renderQualityTable(container, checks) {
        container.innerHTML = "";
        if (!checks) return;

        Object.values(checks).forEach(c => {
            const row = document.createElement("div");
            row.className = "quality-row";

            let pillClass = "pass";
            let pillText = "✅ Pass";
            if (c.status === "fail") {
                pillClass = "fail";
                pillText = "❌ Fail";
            } else if (c.message && c.message.includes("auto-correct")) {
                pillClass = "warning";
                pillText = "⚠️ Corrected";
            }

            row.innerHTML = `
                <div>
                    <span class="quality-name">${c.name}</span>
                    <div class="quality-val">${c.value || ''} &bull; ${c.message}</div>
                </div>
                <span class="status-pill ${pillClass}">${pillText}</span>
            `;
            container.appendChild(row);
        });
    }

    // -------------------------------------------------------------
    // Helper Utilities
    // -------------------------------------------------------------
    function setButtonLoading(btn, spinner, isLoading) {
        const textSpan = btn.querySelector(".btn-text");
        btn.disabled = isLoading;
        if (isLoading) {
            if (textSpan) textSpan.classList.add("hidden");
            if (spinner) spinner.classList.remove("hidden");
        } else {
            if (textSpan) textSpan.classList.remove("hidden");
            if (spinner) spinner.classList.add("hidden");
        }
    }

    function showToast(message, type = "success") {
        appToast.innerText = message;
        appToast.className = `toast ${type}`;
        appToast.classList.remove("hidden");
        setTimeout(() => {
            appToast.classList.add("hidden");
        }, 4000);
    }
});
