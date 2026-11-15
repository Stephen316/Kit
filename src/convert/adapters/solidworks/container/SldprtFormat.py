# the sldprt format contract needs a dedicated boundary so stream contents retain their geometry and feature relationships
class SldprtFormat(ValueError):
    KSlots = ()
