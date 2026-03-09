console.log("🔥 Telegram Bet Bot: Monitorando Bet365 🔥");

// A URL da sua API no Render. 
const API_URL = "https://bot-dze4.onrender.com/bet";

function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Função para buscar as configurações salvas pelo Tipster no popup
async function loadConfig() {
    return new Promise((resolve) => {
        chrome.storage.local.get(['botAtivo', 'senhaPainel', 'grupoDestino', 'tipsterName'], (result) => {
            resolve({
                ativo: result.botAtivo !== false, // Padrão é true
                senha: result.senhaPainel || "",
                grupo: result.grupoDestino || "vip",
                tipster: result.tipsterName || "Anônimo"
            });
        });
    });
}

// Tenta raspar os dados visíveis no Boletim de Apostas (Bet Slip)
function rasparDadosBoletim() {
    // NOTA IMPORTANTE: A Bet365 tem classes ofuscadas e dinâmicas, então os seletores 
    // costumam mudar com o tempo. Estes são seletores genéricos/típicos.
    // É recomendado você inspecionar a página e atualizar as classes se necessário.
    try {
        // Tenta achar o título do Jogo/Evento
        let jogoEl = document.querySelector('.bs-ParticipantFixtureDetails_Fixture') ||
            document.querySelector('.bs-SelectionFixtureDetails_Fixture');

        // Tenta achar o Mercado (Ex: Vencedor do Encontro)
        let mercadoEl = document.querySelector('.bs-MarketDescription_Label') ||
            document.querySelector('.bs-SelectionMarketDetails_Market');

        // Tenta achar a Seleção específica (Ex: Arsenal) 
        let selecaoEl = document.querySelector('.bs-SelectionDetails_Selection') ||
            document.querySelector('.bs-ParticipantName_Name');

        // Tenta achar a Odd do bilhete
        let oddEl = document.querySelector('.bs-Odds') ||
            document.querySelector('.bs-ParticipantOdds_Odds');

        // Valor da Stake apostada (Opcional, só pra constar)
        let stakeEl = document.querySelector('.bs-StakeInput_Input');

        if (!jogoEl || !oddEl) {
            console.warn("Bet Bot: Boletim não encontrado ou incompleto na tela.");
            return null;
        }

        const jogo = jogoEl.innerText.trim();
        const mercadoBase = mercadoEl ? mercadoEl.innerText.trim() : "Mercado Padrão";
        const selecao = selecaoEl ? selecaoEl.innerText.trim() : "Opção Única";
        const mercadoFinal = `${mercadoBase} - ${selecao}`;
        const odd = oddEl.innerText.trim();
        const stake = stakeEl ? stakeEl.value : "";
        const link = window.location.href;

        return {
            jogo: jogo,
            mercado: mercadoFinal,
            odd: odd,
            unidades: stake ? `R$ ${stake}` : "N/A",
            link: link
        };

    } catch (e) {
        console.error("Bet Bot: Erro ao raspar DOM", e);
        return null;
    }
}

async function enviarParaRender(apostaData) {
    const config = await loadConfig();

    if (!config.ativo) {
        console.log("Bet Bot: Bot está pausado na extensão, cancelando envio.");
        return;
    }

    if (!config.senha) {
        alert("Telegram Bet Bot: Favor configurar a Senha do Painel clicando na extensão!");
        return;
    }

    // Prepara o Payload final exatamente como o server.py exige
    const payload = {
        senha: config.senha,
        grupo: config.grupo,
        tipster: config.tipster,
        tipo_aba: 'futebol',      // Padrão que definimos para apostas esportivas normais
        modo_envio: 'resumido',   // Usamos 'resumido' para enviar de forma rápida
        jogo: apostaData.jogo,
        mercado: apostaData.mercado,
        odd: apostaData.odd,
        unidades: apostaData.unidades,
        link: apostaData.link
    };

    console.log("Bet Bot: Disparando POST para o Backend Render:", payload);

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const respJSON = await response.json();

        if (response.ok) {
            console.log("✅ Bet Bot: Sucesso!", respJSON);
            // Mostrar um alerta verde discreto na tela
            mostrarNotificacaoNaTela("✅ Aposta enviada pro Telegram VIP/FREE!");
        } else {
            console.error("❌ Bet Bot: Erro do Servidor:", respJSON);
            alert("Erro no Telegram Bot: " + (respJSON.error || "Acesso Negado."));
        }

    } catch (err) {
        console.error("❌ Bet Bot: Falha na requisição fetch:", err);
    }
}

// Observa o botão "Fazer Aposta" aparecer e anexa nosso click
function monitorarBotaoAposta() {
    setInterval(() => {
        // Seletor geral do botão Fazer Aposta da Bet365
        const btnPlaceBet = document.querySelector('.bs-BtnPlaceBet') ||
            document.querySelector('.bs-PlaceBetButton') ||
            document.querySelector('.lb-PlaceBetButton');

        // Se achou o botão E ele ainda NÃO tem nosso rastreador (evita click duplicado)
        if (btnPlaceBet && !btnPlaceBet.dataset.botAttached) {
            btnPlaceBet.dataset.botAttached = "true";

            console.log("Bet Bot: Botão de Aposta Encontrado! Grampeando...");

            btnPlaceBet.addEventListener('click', async () => {
                console.log("Botão de aposta clicado!");

                // Pequeno delay pra dar tempo do DOM renderizar qqr coisa final
                await delay(300);

                const data = rasparDadosBoletim();
                if (data) {
                    enviarParaRender(data);
                } else {
                    console.log("Bet Bot: Nenhuma aposta válida raspada no boletim aberto.");
                }
            });
        }
    }, 1500);
}

// Funções Cosméticas
function mostrarNotificacaoNaTela(msg) {
    const div = document.createElement("div");
    div.innerText = msg;
    div.style.position = "fixed";
    div.style.bottom = "20px";
    div.style.left = "20px";
    div.style.backgroundColor = "#10b981";
    div.style.color = "#fff";
    div.style.padding = "15px 20px";
    div.style.borderRadius = "8px";
    div.style.zIndex = "999999";
    div.style.fontWeight = "bold";
    div.style.fontSize = "14px";
    div.style.boxShadow = "0px 4px 15px rgba(0,0,0,0.3)";
    div.style.transition = "opacity 0.5s";

    document.body.appendChild(div);

    setTimeout(() => { div.style.opacity = "0"; setTimeout(() => div.remove(), 500); }, 3000);
}

// Inicia o loop de monitoramento
monitorarBotaoAposta();
