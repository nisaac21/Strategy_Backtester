import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(

    children=[
        dbc.NavItem(dbc.NavLink("Strategy Backtest",
                    href="/strategy-results")),
        dbc.NavItem(dbc.NavLink("About Me", href="/about-me")),
    ],
    brand="Quantitative Momemntum Strategy Viability",
    brand_href="#"
)
