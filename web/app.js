"use strict";

const $ = (id) => document.getElementById(id);

const descricao = $("descricao");
const btnGerar = $("btn-gerar");
const painelErro = $("erro");
const painelCarregando = $("carregando");
const painelResultado = $("resultado");
const elMapa = $("mapa");
const elRelatorio = $("relatorio");
const elMetricas = $("metricas");

function mostrar(el) { el.classList.remove("oculto"); }
function ocultar(el) { el.classList.add("oculto"); }

function basename(caminho) {
    if (!caminho) return "";
    return caminho.split(/[\\/]/).pop();
}

function metrica(valor, legenda) {
    return `<div class="metrica"><div class="valor">${valor}</div><div class="legenda">${legenda}</div></div>`;
}

function preencherResultado(estado) {
    const req = estado.requisitos || {};

    // Métricas
    const cartoes = [];
    if (estado.distancia_real_calculada != null) {
        cartoes.push(metrica(`${estado.distancia_real_calculada} km`, "Distância da rota"));
    }
    if (req.distancia_alvo_km != null) {
        cartoes.push(metrica(`${req.distancia_alvo_km} km`, "Distância alvo"));
    }
    if (req.modalidade) cartoes.push(metrica(req.modalidade, "Modalidade"));
    if (req.janela_temporal) cartoes.push(metrica(req.janela_temporal, "Quando"));
    if (req.perfil_altimetria) cartoes.push(metrica(req.perfil_altimetria, "Altimetria"));
    elMetricas.innerHTML = cartoes.join("");

    // Mapa Folium (interativo) servido em /data/<arquivo>
    const arquivoMapa = basename(estado.caminho_mapa_html);
    if (arquivoMapa) {
        elMapa.src = `/data/${arquivoMapa}`;
        mostrar(elMapa.parentElement);
    } else {
        ocultar(elMapa.parentElement);
    }

    // Avaliação final (relatório do Comunicador).
    elRelatorio.textContent = estado.relatorio_narrativo || "Relatório não disponível.";

    mostrar(painelResultado);
}

async function gerarRota() {
    const texto = descricao.value.trim();
    ocultar(painelErro);
    ocultar(painelResultado);

    if (!texto) {
        painelErro.textContent = "Descreva o seu treino antes de gerar a rota.";
        mostrar(painelErro);
        return;
    }

    btnGerar.disabled = true;
    mostrar(painelCarregando);

    try {
        const resp = await fetch("/rotas", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ texto_descritivo: texto }),
        });

        const dados = await resp.json().catch(() => ({}));

        if (!resp.ok) {
            const detalhe = dados.detail || `Erro ${resp.status} ao gerar a rota.`;
            throw new Error(detalhe);
        }

        preencherResultado(dados);
    } catch (e) {
        painelErro.textContent = `Não foi possível gerar a rota: ${e.message}`;
        mostrar(painelErro);
    } finally {
        btnGerar.disabled = false;
        ocultar(painelCarregando);
    }
}

btnGerar.addEventListener("click", gerarRota);

// Ctrl/Cmd + Enter envia
descricao.addEventListener("keydown", (ev) => {
    if ((ev.ctrlKey || ev.metaKey) && ev.key === "Enter") gerarRota();
});
