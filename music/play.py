from music.song.song import Song

song = Song.from_yaml("/Users/harryrackmil/PycharmProjects/music/music/songs/song2.yaml")
song.play()
song.save("song2.wav")