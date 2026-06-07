"""HTTP transport layer. Routers are thin adapters: they parse the request, delegate to
an application service, and return its view model -- no business logic lives here.
"""
