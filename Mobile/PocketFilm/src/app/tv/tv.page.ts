import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';

import { StorageService } from '../storage.service';
import { ToolsService } from '../tools.service';

@Component({
  selector: 'app-tv',
  templateUrl: './tv.page.html',
  styleUrls: ['./tv.page.scss'],
})
export class TvPage implements OnInit {

  // 电视类型
  public type = '全部'

  // 推荐数据
  public recommendations = []
  // 央视台名称
  public cctvName = '央视台'
  // 卫视台名称
  public satelliteTVName = '卫视台'
  // 地方台名称
  public localStationName = '地方台'
  // 港澳台名称
  public hongkongMacaoTaiwanName = '港澳台'
  // 海外台名称
  public overseasStationName = '海外台'
  // 轮播台名称
  public carouselName = '轮播台'

  // 最新排名前10的央视台
  public top10CCTVList = []
  // 最热排名前10的卫视台
  public top10SatelliteList = []
  // 最新排名前10的地方台
  public top10LocalStationList = []
  // 最热排名前10的港澳台
  public top10hongkongMacaoTaiwanList = []
  // 最新排名前10的海外台
  public top10overseasStationList = []
  // 最热排名前10的轮播台
  public top10CarouselList = []

  // 每行电影的数量
  public col_size = 4

  // 影视选中二级类型列表
  public selectTypeList = null
  // 当前页码
  public pageIndex = 1
  // 每页大小
  public pageSize = 9
  // 关键词
  public keyWord = 'null'
  public source_index = 0;
  public type_index = 0;
  // 浏览类型
  public browse_type = 'tv'

  // 当前选中的电视类型
  public selectedType = '全部'

  constructor(
    public storage: StorageService,
    public tools: ToolsService,
    public router: Router
  ) { 
    // 清空缓存
    this.clearCache()
    // 获取电视列表
    this.getTvs()
  }

  ngOnInit() {
  }

  /**
   * 获取电视列表
   */

  getTvs() {
    // 央视台
    this.getTop10Tvs(this.cctvName).then((data: any) => { this.top10CCTVList = data })
    // 卫视台
    this.getTop10Tvs(this.satelliteTVName).then((data: any) => { this.top10SatelliteList = data })
    // 地方台
    this.getTop10Tvs(this.localStationName).then((data: any) => { this.top10LocalStationList = data })
    // 港澳台
    this.getTop10Tvs(this.hongkongMacaoTaiwanName).then((data: any) => { this.top10hongkongMacaoTaiwanList = data })
    // 海外台
    this.getTop10Tvs(this.overseasStationName).then((data: any) => { this.top10overseasStationList = data })
    // 轮播台
    this.getTop10Tvs(this.carouselName).then((data: any) => { this.top10CarouselList = data })
  }

  /**
   * 获取最新排名前10的电视
   * @param type 电视类型
   */

  getTop10Tvs(type): any {
    var top10Tvs = []
    var promise = new Promise((resolve, reject) => {
      var movies = this.storage.get('tv-' + type)
      if (movies == null || movies.length == 0) {
        // 本地没有相应的缓存
      this.tools.getTvListApi(type, this.selectedType, this.pageIndex, this.pageSize, this.keyWord).then((data: any) => {
        if (data.code == 0) {
          top10Tvs = data.data
          this.storage.set('tv-' + type, top10Tvs)
          resolve(top10Tvs)
        }
      })
    } else {
      // 本地有相应的缓存
      resolve(movies)
    }
    })
    return promise
  }

  /**
   * 跳转到电视详情页
   * @param _id 电视_id
   */

  goTvDetail(_id) {
    //  跳转到影视详情页
    this.router.navigate(['/tv-detail'], {
      queryParams: {
        _id: _id
      }
    })
  }

  /**
   * 跳转到更多推荐页
   */

  goMoreRecommendations() {
    this.router.navigate(['/more-recommend-tv'], {
      queryParams: {
        type: this.type
      }
    })
  }

  /**
   * 跳转到更多电视页
   */

  goMoreTv(type) {
    this.router.navigate(['/more-tv'], {
      queryParams: {
        type: type
      }
    })
  }

  /**
   * 跳转到搜索电视页
   */

  goSearchTv() {
    this.router.navigate(['/search-tv'], {
      queryParams: {
        type: this.type,
      }
    })
  }

  /**
   * 下拉刷新
   * @param event 事件对象
   */

  doRefresh(event) {
    // 清空缓存
    this.clearCache()
    // 清空电视列表数据
    this.recommendations = []
    this.top10CCTVList = []
    this.top10SatelliteList = []
    this.top10LocalStationList = []
    this.top10hongkongMacaoTaiwanList = []
    this.top10overseasStationList = []
    this.top10CarouselList = []
    // 修改当前页码
    this.pageIndex = 1
    // 获取电视列表
    this.getTvs()
    if (event) {
      //告诉ionic 刷新数据完成
      event.target.complete();
    }
  }

  /**
   * 清空缓存
   */

  clearCache() {
    // 清空对应的缓存数据
    this.storage.set('tv-recommendations', [])
    this.storage.set('tv-央视台', [])
    this.storage.set('tv-卫视台', [])
    this.storage.set('tv-地方台', [])
    this.storage.set('tv-港澳台', [])
    this.storage.set('tv-海外台', [])
    this.storage.set('tv-轮播台', [])
  }

}
