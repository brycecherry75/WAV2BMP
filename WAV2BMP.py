import argparse, struct, sys, os, ctypes, BMPoperations, WAVoperations

if __name__ == "__main__":

  parser = argparse.ArgumentParser(fromfile_prefix_chars='@')
  parser.add_argument("--wavfile", help="WAV file input")
  parser.add_argument("--channel", type=int, default=0, help="WAV file channel (default: 0)")
  parser.add_argument("--bmpfile", help="BMP file to generate")
  parser.add_argument("--xres", type=int, default=0, help="X resolution in pixels")
  parser.add_argument("--yres", type=int, default=0, help="Y resolution in pixels")

  args = parser.parse_args()
  wavfilename = args.wavfile
  bmpfilename = args.bmpfile
  X_resolution = args.xres
  Y_resolution = args.yres
  ValidParameters = True

  if not args.bmpfile:
    ValidParameters = False
    print("ERROR: BMP output file not specified")
  if not args.xres:
    ValidParameters = False
    print("ERROR: X resolution is not specified")
  elif X_resolution < 1 or X_resolution > 65535:
    ValidParameters = False
    print("ERROR: X resolution is out of range")
  if not args.yres:
    ValidParameters = False
    print("ERROR: Y resolution is not specified")
  elif Y_resolution < 1 or Y_resolution > 65535:
    ValidParameters = False
    print("ERROR: Y resolution is out of range")
  if ValidParameters == True and BMPoperations.CalculateFileSize(X_resolution, Y_resolution, 1) == 0:
    ValidParameters = False
    print("ERROR: Attempt to create BMP file with size over 4294967295 bytes")
  if not args.wavfile:
    ValidParameters = False
    print("ERROR: WAV input file not specified")
  elif not os.path.isfile(wavfilename):
    ValidParameters = False
    print("ERROR:", wavfilename, "not found")

  if ValidParameters == True:
    SelectedChannel = args.channel
    wavfilesize = os.path.getsize(wavfilename)
    wavbuffer = (ctypes.c_byte * wavfilesize)()
    wavfile = open(wavfilename, 'rb')
    wavbuffer = wavfile.read(wavfilesize)
    Channels = WAVoperations.ReadChannelCount(wavbuffer)
    BitDepth = WAVoperations.ReadBitDepth(wavbuffer)
    SampleRate = WAVoperations.ReadSampleRate(wavbuffer)
    SampleCount = WAVoperations.ReadSampleCount(wavbuffer)
    ErrorCode = WAVoperations.CheckValidFormat(wavbuffer)

    if ErrorCode != WAVoperations.ERROR_NONE:
      ValidParameters = False
      print("Error code", ErrorCode, "- refer to WAVoperations.py for definition")
    elif SelectedChannel < 0 or SelectedChannel > Channels:
      ValidParameters = False
      print("ERROR: Channel is out of range for", wavfilename)
    elif WAVoperations.CheckAudioIsUncompressed(wavbuffer) == False:
      ValidParameters = False
      print("ERROR:", wavfilename, "is compressed and therefore unsuitable for WAVoperations")

    if ValidParameters == True:
      FileSize = BMPoperations.CalculateFileSize(X_resolution, Y_resolution, 1)
      bmpbuffer = (ctypes.c_byte * FileSize)()
      for ByteToClear in range (len(bmpbuffer)):
        bmpbuffer[ByteToClear] = 0x00
      bmpbuffer = BMPoperations.WriteHeader(X_resolution, Y_resolution, 1, 2835, 2835, bmpbuffer)
      PaletteBuffer = (ctypes.c_byte * (2 * 3))()
      PaletteBuffer[0] = 0
      PaletteBuffer[1] = 0
      PaletteBuffer[2] = 0
      PaletteBuffer[3] = 255
      PaletteBuffer[4] = 255
      PaletteBuffer[5] = 255
      BMPoperations.WritePalette(PaletteBuffer, bmpbuffer)

      HorizontalIncrement = X_resolution / SampleCount
      VerticalIncrement = Y_resolution / (1 << BitDepth)
      HalfVertical = Y_resolution / 2
      LineStart_X = 0
      LineStart_Y = HalfVertical
      for WaveformPoint in range (SampleCount):
        WaveformData = WAVoperations.ReadSample(SelectedChannel, WaveformPoint, wavbuffer)
        WaveformData *= VerticalIncrement
        WaveformData += HalfVertical
        NewLineStart_X = int(WaveformPoint * HorizontalIncrement)
        NewLineStart_Y = int(Y_resolution - WaveformData)
        if WaveformPoint > 0:
          BMPoperations.DrawLine(LineStart_X, LineStart_Y, NewLineStart_X, NewLineStart_Y, 1, bmpbuffer)
        LineStart_X = NewLineStart_X
        LineStart_Y = NewLineStart_Y

      bmpfile = open(bmpfilename, 'wb')
      bmpfile.write(bmpbuffer)
      bmpfile.close()
      print("BMP file write complete")

    wavfile.close()