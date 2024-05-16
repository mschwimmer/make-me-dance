async function fetchPlaylists() {
    try {
        const response = await fetch('/user-playlists');
        const data = await response.json();
        console.log('Playlists', data);
        return data;
    } catch (error) {
        console.error('Error fetching user playlists', error)
        throw error;
    }
}

async function fetchPlaylistItems(playlists) {
    try {
        const response = await fetch('/playlist-items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(playlists)
        });
        const data = await response.json();
        console.log('Playlist items', data);
        return data;
    } catch (error) {
        console.error('Error fetching playlist items', error)
        throw error;
    }
}

async function getAllSongData() {
    try {
        console.log('Call user-playlists route');
        var playlists = await fetchPlaylists();
        if (playlists.length > 0) {
            console.log('Call playlist-items route');
            playlists = await fetchPlaylistItems(playlists);
            return playlists
        } else {
            console.log('No Playlists available');
        }
    } catch (error) {
        console.error('Error Failed to get playlists or items')
    }


}

getAllSongData().then(data => {
    if (data) {
        console.log('got data!', data);
    }
});
console.log('Finished running js function');