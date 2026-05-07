import reflex as rx

DARK_BG   = "#0A0A0F"
SURFACE   = "#13131A"
ACCENT    = "#FF6B00"
GRADIENT  = "linear-gradient(135deg, #FF6B00 0%, #FFB347 100%)"

def nav_link(label: str, href: str, icon: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.icon(tag=icon, size=16),
            rx.text(label, size="2", weight="medium"),
            spacing="2",
            align="center",
        ),
        href=href,
        class_name="nav-link",
        text_decoration="none",
    )

def navbar() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Logo
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.text("M", weight="bold", size="4", color="white"),
                        width="32px", height="32px",
                        background=GRADIENT,
                        border_radius="8px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.text(
                        "MÁNDALO",
                        weight="bold",
                        size="4",
                        style={"background": GRADIENT,
                               "-webkit-background-clip": "text",
                               "-webkit-text-fill-color": "transparent",
                               "background-clip": "text"},
                    ),
                    spacing="2",
                    align="center",
                ),
                href="/dashboard",
                text_decoration="none",
            ),

            rx.spacer(),

            # Links de navegación
            rx.hstack(
                nav_link("Dashboard", "/dashboard", "layout-dashboard"),
                nav_link("Mapa",      "/map",       "map-pin"),
                nav_link("KYC",       "/kyc",       "shield-check"),
                nav_link("Wallet",    "/wallet",    "wallet"),
                spacing="1",
            ),

            rx.spacer(),

            # Botón de logout
            rx.button(
                rx.hstack(
                    rx.icon(tag="log-out", size=14),
                    rx.text("Salir", size="2"),
                    spacing="1",
                ),
                on_click=rx.redirect("/"),
                size="2",
                variant="ghost",
                color_scheme="gray",
            ),

            width="100%",
            padding_x="2rem",
            align="center",
        ),
        position="sticky",
        top="0",
        left="0",
        right="0",
        z_index="100",
        background=f"rgba(10, 10, 15, 0.85)",
        backdrop_filter="blur(16px)",
        border_bottom=f"1px solid rgba(255, 255, 255, 0.06)",
        height="60px",
        display="flex",
        align_items="center",
    )
