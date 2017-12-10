package main

func main() {
	config := readConfig()
	SetupDb(config)
}
