#!/bin/bash
python initialize_data.py

chmod 664 ./services/listings/listings.db
chmod 664 ./services/users/users.db