package main

import (
	"fmt"
	"log"
	"os"

	"github.com/jinzhu/gorm"
	_ "github.com/jinzhu/gorm/dialects/postgres"
)

// model for the meme database
type Meme struct {
	gorm.Model

	Name          string `gorm:"unique"`
	Transcription string `gorm:"type:text"`
	Notes         string `gorm:"type:text"`
	MinioId       string
	Format        MemeFormat
	// this determines whether the meme is the original one for the format
	Original bool
}

// model for the memeformat database
type MemeFormat struct {
	gorm.Model

	Name        string `gorm:"unique"`
	Description string `gorm:"type:text"`
}

// return an instance of the database. Note: you should close this when you are done with it
func getDb(config *Config) *gorm.DB {
	connectionString := fmt.Sprintf("host=%s user=%s dbname=%s sslmode=disable password=%s",
		config.PgHost,
		config.PgUser,
		config.PgDatabase,
		config.PgPass,
	)
	db, err := gorm.Open("postgres", connectionString)

	if err != nil {
		log.Fatalf("Could not connect to database\n%v\n", err)
		os.Exit(1)
	}

	return db
}

// create the tables if they do not exist
// run this on startup
func SetupDb(config *Config) {
	db := getDb(config)
	defer db.Close()

	db.AutoMigrate(&Meme{})
	db.AutoMigrate(&MemeFormat{})
}
