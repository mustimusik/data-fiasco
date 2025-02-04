import ffmpeg

audio_input = ffmpeg.input("full_song.mp3")
audio_cut = audio_input.audio.filter('atrim', duration=1)
audio_output = ffmpeg.output(audio_cut, 'trimmed_output_ffmpeg.mp3', format='mp3')
ffmpeg.run(audio_output)