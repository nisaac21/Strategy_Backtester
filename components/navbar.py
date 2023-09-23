import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(

    children=[
        dbc.NavItem(dbc.NavLink("Strategy Backtest",
                    href="/strategy-results")),
        # dbc.NavItem(dbc.NavLink("About Me", href="/about-me")), # TODO: BUILD OUT
    ],
    brand="Quantitative Momemntum Strategy Viability",
)
