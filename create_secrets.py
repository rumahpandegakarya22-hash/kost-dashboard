import toml

secrets = {
    'auth': {
        'credentials': {
            'usernames': {
                'executive': {'name': 'Executive', 'password': '$2b$12$IFNO1kcDLpfpUWIoIzE/peWTF7.mAw631cGe9QAnBBpssFHhbPV6G'},
                'sales': {'name': 'Sales', 'password': '$2b$12$6cW1wEzHNpNcYtPYSIyk0.DoLVeL6gzAnCjglBKQQ9thS7JJYcIym'},
                'admin': {'name': 'Admin', 'password': '$2b$12$hQQHj1fyOlN.ANzZd0zIoeLgyY2YE8M02jvRt.CANT99MGF7s0eZy'},
                'marketing': {'name': 'Marketing', 'password': '$2b$12$qAALj9RqnWODV7Dipf/RL.9HbVh3UD.waFcBSNwfKZg42/jDruscS'},
                'operasional': {'name': 'Operasional', 'password': '$2b$12$mLHZJxAOpSn7z4YDBDo/6.XBxRiIrbctJlj5eDBPkkgfwjJUTS1om'}
            }
        },
        'cookie': {'name': 'Dashboard Kost', 'key': 'IYiaKo7KuPlbShE2GWO2DbDrj1WRBNuZvlCthAJI57A'}
    },
    'connections': {
        'gsheets': {
            'type': 'service_account',
            'project_id': 'dashboard-ktd-v2',
            'private_key_id': 'ce2a969fd3c1d830e12ce1ce686e56e7162b8f48',
            'private_key': '-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCs65xEBwAbWM3n\n4RaSRJ341pF2st2hJYraS0CuGrnd52ylSh91yBuwSOiyxqaxqbq0Gm1w1JFA0TvD\nlKtC/7Q7rBmOCFpA1Kqo2tREebMn2S+T5Ux90ZW676G1N+Kq2zUqCMJhcnAIXF7/\n3hj2ufi5NnIqsjCtvQTHulDoVUo8+XPiH74wdSJfXHdtJOKpJYMWFbwOLeMR1Jyo\nFb7YOix7oZ/Bwvt/fSRr7CvezKYqUcJnhysQ/wr2Bgvu70OYZW0G5WarcQaZnyLJ\n4H6PIl609bNalQ+47zwOCoYqHlUozhcH8cwo17LeWZkvFKG9a3FJ/aJ8SvncEo7n\ne3l+TqK1AgMBAAECggEAUH/xA/RUVubNGJU/akF6X0UYe+9B4Qq2rPAagNLdU1Iw\n0HQE2FKbnUIb3lo/cPcIfV7OMxgqNMgTL/Yukmay05LHZMk7pvG6LxiMeAJF5pej\noBC/vtUKhPeYyuHk6lBZXCOuxim9wQ6rhScybO3fve18UacZpVAZARgaIUbPZDmi\n/X2EZ58+nsJbtFb70j1vz+4HMZSoHiwrIRr5+wHY7extOtMAt12BP2SP5m+5ia5A\nem+wg6D3SqE45mK/nSTfYPKwDG01jqIW39eldTRLZShT1fXsbOl5PnUZNg++OheS\nWwlMqiISeFAq/vFw2YYzG3UA9Vu+XO81NERnd25PwwKBgQDY7OFz7Ttc4sQaTpOe\nC9T7i/yFODO4IgoL/Q3Yo1HGrRjUxrmgdvqyQIapJjdzDoC7sb2utRdTkuC7+w42\nZyIAfolvrXfCWaPrNwOQy+Ih79zfC5QQ+/GgUzxFEF64bQyNtQkyUKr6+QQZcu5o\nwsBTKTafluWl6RwFZJeNzA9FAwKBgQDMEYU101hlW20o4F5tOFU9jwIq8fQYZPZs\n9nr1MEpDwBUVAsM2TbG8WXjfy9sB4nidaoyda58PkvgbQeEGv8pEwecqHLyL55yw\nrMYR0tON6N1/cg8AFQhDa8cpomBx+rW7IHDOvrcE8hHyLTH+EUTKWTaSgZsuvzDn\nEKcH2mQf5wKBgAt6nYOQ7i9AILhzqAQZBDA7fCVgj/wScQ2pWm44Vj95MXMxAOmo\n4iNEntuclhqUjeNgyHTSSGW3xASuiFYApx/3kjZCq6+xJqdvxdSHtXOuSbXT2wX7\nDxI41VuiPiDsRFnLVq0+741QWBMwrcUFaT/9UlKnnYdmCoGOjSaHwdcZAoGBAJQc\nS0DLyiaWet3mKuK+ti9dskcVIQLrlGd1Zby7dctCiIqdXK33Kf74OWDFBomRo9Us\n1i4TRHj7RJQT9oz9eoL48RyBit9IFVOtsnyRNfaTgt/TGswGd97nRMAVGEbhnjDY\n1MdZaGBwiVHqN5SdV/49Tfx7kPQW1BmA3po2ieEVAoGBAIriuSXqhgQc3XYQxgFQ\n+j/08GU7XuWbHG0v2Ly7KqfQmaDlJCimNW85+gunDPVKfiU0v+EWsm34WWDzrlKt\nWmlQz2+wOQxBV3xEnurojaeX1L7TopWLzpCssRTUCCKi2wxpsLefa9wbWJZb3Rdk\nStGQKMpBvRtJMbe5MFs3xW1g\n-----END PRIVATE KEY-----\n',
            'client_email': 'dashboardv2@dashboard-ktd-v2.iam.gserviceaccount.com',
            'client_id': '104768527265335025585',
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://oauth2.googleapis.com/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/dashboardv2%40dashboard-ktd-v2.iam.gserviceaccount.com',
            'spreadsheet': 'https://docs.google.com/spreadsheets/d/11pe-ubcLyHDGgG5v01mRZmItIsreiKp_/edit'
        }
    }
}

with open('.streamlit/secrets.toml', 'w') as f:
    toml.dump(secrets, f)

print('secrets.toml created successfully!')