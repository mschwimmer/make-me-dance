function updateDanceSongs() {
    fetch('/get-user-song-data')
        .then(response => response.json())
        .then(data => {
            console.log('Data received, parsing data now');
            var songTable = '';
            console.log('Data type: ',typeof data);
            // Create a table row for each song
            data.forEach((song, index) => {
//                console.log(song);
                songTable += `
                <tr>
                    <th scope="row">${index + 1}</th>
                    <td>${song.track_name}</td>
                    <td>${song.album}</td>
                    <td>${song.artist}</td>
                    <td>${song.plist_name}</td>
                    <td>${song.danceability}</td>
                </tr>`;
            });
//            data.forEach((song) => {console.log(song)});

            // Replace the existing table content
            document.querySelector('.table tbody').innerHTML = songTable;

            // Update the h1 tag in the loading message
            document.getElementById('loading-message').querySelector('h1').textContent = "Successfully retrieved your dance songs!";

            // Delete the snarky p tags
            const pTags = document.getElementById('loading-message').querySelectorAll('p');
            pTags.forEach((p) => {
            p.remove()
            });

            // Start displaying all the content in our data-container div
            document.querySelector('.data-container').style.removeProperty("display");
//            document.querySelector('#loading-message').style.display = 'none';
            });
}

console.log('Call js function');
updateDanceSongs();
console.log('Finished running js function');