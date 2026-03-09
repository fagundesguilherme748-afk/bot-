document.addEventListener('DOMContentLoaded', () => {
    const chkBotAtivo = document.getElementById('botAtivo');
    const iptSenha = document.getElementById('senha');
    const selGrupo = document.getElementById('grupoDestino');
    const iptTipster = document.getElementById('tipsterName');
    const btnSalvar = document.getElementById('btnSalvar');
    const statusMsg = document.getElementById('statusMsg');

    // Carregar dados salvos
    chrome.storage.local.get(['botAtivo', 'senhaPainel', 'grupoDestino', 'tipsterName'], (result) => {
        if (result.botAtivo !== undefined) chkBotAtivo.checked = result.botAtivo;
        if (result.senhaPainel) iptSenha.value = result.senhaPainel;
        if (result.grupoDestino) selGrupo.value = result.grupoDestino;
        if (result.tipsterName) iptTipster.value = result.tipsterName;
    });

    // Salvar configurações
    btnSalvar.addEventListener('click', () => {
        const dados = {
            botAtivo: chkBotAtivo.checked,
            senhaPainel: iptSenha.value,
            grupoDestino: selGrupo.value,
            tipsterName: iptTipster.value
        };

        chrome.storage.local.set(dados, () => {
            statusMsg.style.display = 'block';
            setTimeout(() => {
                statusMsg.style.display = 'none';
            }, 2000);
        });
    });
});
