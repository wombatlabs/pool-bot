package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"time"

	tgbotapi "github.com/go-telegram-bot-api/telegram-bot-api"
)

const (
	apiURL           = "https://example.org/api/blocks"
	botToken         = "270485614:AAHfiqksKZ8WmR2zSjiQ7_v4TMAKdiHm9T0"
	CHANNEL_USERNAME = "@username"
	updateInterval   = 10 * time.Minute // Update interval for checking the latest height
)

type BlockData struct {
	Hash      string
	Finder    string
	Coin      string
	Height    int
	Timestamp string
}

// Function to get the chat ID for a given channel username
func getChatID(bot *tgbotapi.BotAPI, username string) (int64, error) {
	chat, err := bot.GetChat(tgbotapi.ChatConfig{SuperGroupUsername: username})
	if err != nil {
		return 0, err
	}
	return chat.ID, nil
}

func main() {
	bot, err := tgbotapi.NewBotAPI(botToken)
	if err != nil {
		log.Panicf("Error connecting to Telegram Bot API: %v", err)
	}

	bot.Debug = true

	log.Printf("Connected to Telegram as %s", bot.Self.UserName)

	// Get the actual channel ID
	channelID, err := getChatID(bot, CHANNEL_USERNAME)
	if err != nil {
		log.Printf("Error getting channel ID: %v", err)
		return
	}

	// Initialize lastHeight with an invalid value to force sending the first update
	lastHeight := -1

	for {
		poolStats, err := getPoolStats()
		if err != nil {
			log.Printf("Error fetching pool statistics: %v", err)
		} else {
			if poolStats.Height != lastHeight {
				// Update the lastHeight
				lastHeight = poolStats.Height

				msg := tgbotapi.NewMessage(channelID, fmt.Sprintf("New block found.\nCoin: %s\nHeight: %d\nTimestamp: %s\nFinder: %s",
					poolStats.Coin, poolStats.Height, poolStats.Timestamp, poolStats.Finder))

				// Send the message to the specified channel
				bot.Send(msg)
			}
		}

		// Wait for the specified update interval before checking again
		time.Sleep(updateInterval)
	}
}

func getPoolStats() (*BlockData, error) {
	resp, err := http.Get(apiURL)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()

	var poolStats map[string]interface{}
	err = json.NewDecoder(resp.Body).Decode(&poolStats)
	if err != nil {
		return nil, err
	}

	// Extract the "matured" block data
	maturedBlocks, ok := poolStats["matured"].([]interface{})
	if !ok || len(maturedBlocks) == 0 {
		return nil, fmt.Errorf("no matured block data found in the response")
	}

	// Extract the first block's data
	block := maturedBlocks[0].(map[string]interface{})

	// Extract values for height and timestamp
	height := int(block["height"].(float64))
	timestamp := time.Unix(int64(block["timestamp"].(float64)), 0).Format("02/01/2006, 15:04:05")

	// Extract values for coin, hash, and finder
	coin := "ETC-SOLO" // Customize with your desired coin
	hash := block["hash"].(string)
	finder := block["finder"].(string)

	return &BlockData{
		Hash:      hash,
		Finder:    finder,
		Coin:      coin,
		Height:    height,
		Timestamp: timestamp,
	}, nil
}
