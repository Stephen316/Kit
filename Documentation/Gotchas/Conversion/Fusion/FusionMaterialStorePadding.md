# Material store block capacity is not logical payload length

The controlled `.protein` nested archive stores property streams as a 16-byte header followed by 136-byte blocks.
Each block contains a next-block index, a used-byte count, flags, and 128 bytes of capacity.
Unused capacity can contain unrelated allocation residue; treating all 128 bytes as material payload invents fields and can expose incidental process-memory fragments in research dumps.

Follow the chain, validate the used-byte count, and concatenate only those used bytes.
The `0xffffffff` next-index sentinel terminates the chain; the observed flag value 1 marks a start block.

The [envelope model](../../../../re/Fusion/Reconstruction/DocumentEnvelope/EnvelopeRecipe.md) documents the exact build.
The block allocator, definition records, and controlled instance properties are decoded.
The [typed material grammar](../../../../re/Fusion/Reconstruction/ProteinInstances/MaterialGrammar.md) excludes padding and regenerates unused capacity as zero bytes.
