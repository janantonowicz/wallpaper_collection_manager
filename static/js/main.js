$(document).on('click', '.open-wallpaper-modal', function() {
    var wallpaperId = $(this).data('wallpaper-id');
    var collectionId = $(this).data('collection-id');
    $.get('/load_wallpaper_modal', { wallpaper_id: wallpaperId, collection_id: collectionId }, function(data) {
        $('#wallpaperModal .modal-content').html(data);
        $('#wallpaperModal').modal('show');
    });
});