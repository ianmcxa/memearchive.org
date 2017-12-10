package main

import (
	"flag"
	"log"
	"os"

	"github.com/BurntSushi/toml"
)

// type for our configuration file
// NOTE THAT TO DECODE ANYTHNIG YOU NEED THE VARS TO START WITH CAPITAL
// LETTERS
type Config struct {
	PgHost         string
	PgUser         string
	PgPass         string
	PgPort         int
	PgDatabase     string
	MinioHost      string
	MinioAccessKey string
	MinioSecretKey string
	WebPort        int
}

// read in the JSON config file
func readConfig() *Config {
	// read the flag for the optional config file
	configFile := flag.String("conf", "./conf.toml", "Configuration file for memearchive.org")
	flag.Parse()
	// read the configuration file
	config := &Config{}
	_, err := toml.DecodeFile(*configFile, config)

	if err != nil {
		log.Fatalf("Could not parse configuration file\n%v\n", err)
		os.Exit(1)
	}

	return config
}
