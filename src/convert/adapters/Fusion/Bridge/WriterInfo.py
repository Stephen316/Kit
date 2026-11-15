from convert.adapters.Fusion.AdapterInfo import KReaderInfo

# writer info must share the reader info contract so native adapter translation cannot drift between equivalent names
KWriterInfo = KReaderInfo
