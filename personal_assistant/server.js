import express from 'express';
import cors from 'cors';
import { DatabaseSync } from 'node:sqlite';
import path from 'node:path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Connect to SQLite database
const dbPath = path.resolve(__dirname, '../plugins/media_organizer/data/media.db');
const db = new DatabaseSync(dbPath);

// Retrieve all categories
app.get('/api/categories', (req, res) => {
  try {
    const rows = db.prepare(`
      SELECT DISTINCT main_category 
      FROM media 
      WHERE main_category IS NOT NULL AND main_category != ''
      ORDER BY main_category ASC
    `).all();
    const categories = rows.map(r => r.main_category);
    res.json(categories);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Retrieve statistics
app.get('/api/stats', (req, res) => {
  try {
    const totalCount = db.prepare("SELECT COUNT(*) as count FROM media").get().count;
    
    const types = db.prepare(`
      SELECT media_type, COUNT(*) as count 
      FROM media 
      WHERE media_type IS NOT NULL
      GROUP BY media_type
    `).all();

    const categories = db.prepare(`
      SELECT main_category, COUNT(*) as count 
      FROM media 
      WHERE main_category IS NOT NULL AND main_category != ''
      GROUP BY main_category
      ORDER BY count DESC
    `).all();

    res.json({
      total: totalCount,
      types,
      categories
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// List media with filtering, searching, and pagination
app.get('/api/media', (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 12;
    const offset = (page - 1) * limit;

    const { search, category, type, year } = req.query;

    let conditions = [];
    let params = [];

    if (search) {
      conditions.push("(title LIKE ? OR title_ru LIKE ? OR title_orig LIKE ? OR plot LIKE ?)");
      const searchParam = `%${search}%`;
      params.push(searchParam, searchParam, searchParam, searchParam);
    }

    if (category) {
      conditions.push("main_category = ?");
      params.push(category);
    }

    if (type) {
      conditions.push("media_type = ?");
      params.push(type);
    }

    if (year) {
      conditions.push("year = ?");
      params.push(parseInt(year));
    }

    const whereClause = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';

    // Get total matching count
    const countSql = `SELECT COUNT(*) as count FROM media ${whereClause}`;
    const totalCount = db.prepare(countSql).get(...params).count;

    // Get paginated results
    const selectSql = `
      SELECT id, title, title_orig, title_ru, year, main_category, genres, rating, media_type, media_size, path, status
      FROM media 
      ${whereClause} 
      ORDER BY id DESC 
      LIMIT ? OFFSET ?
    `;
    const items = db.prepare(selectSql).all(...params, limit, offset);

    res.json({
      items,
      pagination: {
        page,
        limit,
        totalItems: totalCount,
        totalPages: Math.ceil(totalCount / limit)
      }
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get detailed media card
app.get('/api/media/:id', (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const item = db.prepare("SELECT * FROM media WHERE id = ?").get(id);

    if (!item) {
      return res.status(404).json({ error: 'Media not found' });
    }

    res.json(item);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create new media item
app.post('/api/media', (req, res) => {
  try {
    const {
      title, title_orig, title_ru, year, main_category, genres,
      country, directors, cast, status, num_of_seasons,
      rating, plot, media_type, path, media_size
    } = req.body;

    const stmt = db.prepare(`
      INSERT INTO media (
        title, title_orig, title_ru, year, main_category, genres,
        country, directors, cast, status, num_of_seasons,
        rating, plot, media_type, path, media_size
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const result = stmt.run(
      title || null,
      title_orig || null,
      title_ru || null,
      year ? parseInt(year) : null,
      main_category || null,
      genres || null,
      country || null,
      directors || null,
      cast || null,
      status || 'Scan Completed',
      num_of_seasons ? parseInt(num_of_seasons) : null,
      rating || null,
      plot || null,
      media_type || 'movie',
      path || null,
      media_size ? parseFloat(media_size) : null
    );

    res.status(201).json({ id: result.lastInsertRowid, message: 'Media item created successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Update media details
app.put('/api/media/:id', (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const {
      title, title_orig, title_ru, year, main_category, genres,
      country, directors, cast, status, num_of_seasons,
      rating, plot, media_type, path, media_size,
      atmosphere, why_watch, mood, catchphrases, quote,
      can_stop_at, facts, similar, final_verdict, review
    } = req.body;

    const stmt = db.prepare(`
      UPDATE media SET
        title = ?, title_orig = ?, title_ru = ?, year = ?, main_category = ?, genres = ?,
        country = ?, directors = ?, cast = ?, status = ?, num_of_seasons = ?,
        rating = ?, plot = ?, media_type = ?, path = ?, media_size = ?,
        atmosphere = ?, why_watch = ?, mood = ?, catchphrases = ?, quote = ?,
        can_stop_at = ?, facts = ?, similar = ?, final_verdict = ?, review = ?
      WHERE id = ?
    `);

    stmt.run(
      title || null,
      title_orig || null,
      title_ru || null,
      year ? parseInt(year) : null,
      main_category || null,
      genres || null,
      country || null,
      directors || null,
      cast || null,
      status || null,
      num_of_seasons ? parseInt(num_of_seasons) : null,
      rating || null,
      plot || null,
      media_type || null,
      path || null,
      media_size ? parseFloat(media_size) : null,
      atmosphere || null,
      why_watch || null,
      mood || null,
      catchphrases || null,
      quote || null,
      can_stop_at || null,
      facts || null,
      similar || null,
      final_verdict || null,
      review || null,
      id
    );

    res.json({ message: 'Media item updated successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Delete media item
app.delete('/api/media/:id', (req, res) => {
  try {
    const id = parseInt(req.params.id);
    const stmt = db.prepare("DELETE FROM media WHERE id = ?");
    stmt.run(id);
    res.json({ message: 'Media item deleted successfully' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get episodes of a series
app.get('/api/media/:id/episodes', (req, res) => {
  try {
    const id = parseInt(req.params.id);
    // Find all seasons where parent_id = series_id
    const seasons = db.prepare("SELECT id FROM media WHERE parent_id = ? AND media_type = 'season'").all(id);
    if (seasons.length === 0) {
      return res.json([]);
    }
    const seasonIds = seasons.map(s => s.id);
    // Find all episodes of these seasons
    const placeholders = seasonIds.map(() => '?').join(',');
    const episodes = db.prepare(`
      SELECT * FROM media 
      WHERE parent_id IN (${placeholders}) AND media_type = 'episode' 
      ORDER BY title
    `).all(seasonIds);
    
    // Map to fields expected by app.js: season_number, episode_number, title
    const mapped = episodes.map(ep => {
      // Extract season number from parent season title if needed, or parse title
      // S01E02 title format: S01E02 -> Season 1, Episode 2
      const match = ep.title.match(/S(\d+)E(\d+)/i);
      const season_num = match ? parseInt(match[1]) : 1;
      const episode_num = match ? parseInt(match[2]) : 1;
      return {
        id: ep.id,
        season_number: season_num,
        episode_number: episode_num,
        title: ep.title_ru || ep.title
      };
    });
    res.json(mapped);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running at http://localhost:${PORT}`);
});
