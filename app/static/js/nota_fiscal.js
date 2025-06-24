function buscarItem() {
  const codigo = document.getElementById('codigo').value;
  if (!codigo) return;

  fetch(`/nota/buscar_item?codigo=${codigo}`)
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        document.getElementById('descricao').value = data.descricao;
        document.getElementById('valor').value = data.valor;
      } else {
        alert('Item não encontrado');
        document.getElementById('descricao').value = '';
        document.getElementById('valor').value = '';
      }
    });
}

function adicionarItem() {
  const codigo = document.getElementById('codigo').value;
  const descricao = document.getElementById('descricao').value;
  const quantidade = document.getElementById('quantidade').value;
  const valor = document.getElementById('valor').value;

  if (!codigo || !descricao || !quantidade || !valor) {
    alert('Preencha todos os campos do item.');
    return;
  }

  const tabela = document.getElementById('tabela-itens');
  const row = tabela.insertRow();
  row.innerHTML = `
    <td>
      ${codigo}
      <input type="hidden" name="codigo[]" value="${codigo}">
    </td>
    <td>${descricao}</td>
    <td>
      ${quantidade}
      <input type="hidden" name="quantidade[]" value="${quantidade}">
    </td>
    <td>
      ${valor}
      <input type="hidden" name="valor[]" value="${valor}">
    </td>
    <td>
      <button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove()">Excluir</button>
    </td>
  `;

  document.getElementById('codigo').value = '';
  document.getElementById('descricao').value = '';
  document.getElementById('quantidade').value = '';
  document.getElementById('valor').value = '';
}
