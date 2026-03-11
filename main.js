
document.getElementById('searchAtleta').addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const rows = document.querySelectorAll('table tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
});


document.getElementById('filterEscalao').addEventListener('change', function(e) {
    const escalao = e.target.value;
    const rows = document.querySelectorAll('table tbody tr');
    
    rows.forEach(row => {
        if (!escalao || row.querySelector('td:nth-child(3)').textContent === escalao) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
});


function confirmarRemocao(atletaId, nome) {
    return Swal.fire({
        title: 'Confirmar exclusão',
        text: `Deseja realmente remover o atleta ${nome}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Sim',
        cancelButtonText: 'Não'
    }).then((result) => {
        if (result.isConfirmed) {
            window.location.href = `/remover/${atletaId}`;
        }
    });
}


function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type} fade-in`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}