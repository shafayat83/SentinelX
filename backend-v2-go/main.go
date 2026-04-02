package main

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"net/http"
	"time"
)

// Models
type DetectionJobV2 struct {
	ID           string    `gorm:"primaryKey" json:"id"`
	AOIName      string    `json:"aoi_name"`
	Status       string    `json:"status"` // PENDING, PROCESSING, COMPLETED, FAILED
	Progress     int       `json:"progress"`
	T1Range      string    `json:"t1_range"`
	T2Range      string    `json:"t2_range"`
	ResultURL    string    `json:"result_url"`
	CreatedAt    time.Time `json:"created_at"`
}

var db *gorm.DB

func initDB() {
	dsn := "host=localhost user=admin password=password dbname=makeit port=5432 sslmode=disable"
	var err error
	db, err = gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		panic("failed to connect database")
	}
	db.AutoMigrate(&DetectionJobV2{})
}

func main() {
	r := gin.Default()
	
	// Tactical Hub Endpoints
	r.GET("/api/v2/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "Tactical Intelligence Hub Online"})
	})

	r.POST("/api/v2/jobs", createJob)
	r.GET("/api/v2/jobs/:id", getJob)
	r.GET("/api/v2/jobs", listJobs)

	r.Run(":8080")
}

func createJob(c *gin.Context) {
	var job DetectionJobV2
	if err := c.ShouldBindJSON(&job); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	job.ID = uuid.New().String()
	job.Status = "PENDING"
	job.CreatedAt = time.Now()
	
	db.Create(&job)
	
	// Trigger gRPC call to Python ML Service here
	// go triggerMLInference(job.ID)
	
	c.JSON(http.StatusAccepted, job)
}

func getJob(c *gin.Context) {
	id := c.Param("id")
	var job DetectionJobV2
	if err := db.First(&job, "id = ?", id).Error; err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "Job not found"})
		return
	}
	c.JSON(http.StatusOK, job)
}

func listJobs(c *gin.Context) {
	var jobs []DetectionJobV2
	db.Find(&jobs)
	c.JSON(http.StatusOK, jobs)
}
